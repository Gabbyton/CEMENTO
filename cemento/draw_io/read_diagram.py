from os import path

import pandas as pd
from bs4 import BeautifulSoup
from defusedxml import ElementTree as ET

from cemento.draw_io.diagram import Diagram
from cemento.draw_io.diagram_errors import (
    BlankEdgeLabelError,
    BlankTermLabelError,
    CircularEdgeError,
    DisconnectedTermError,
    FloatingEdgeError,
    MissingChildEdgeError,
    MissingParentEdgeError,
    WrongFileFormatError,
)
from cemento.draw_io.diagram_ref import DiagramRef


class ReadDiagram(Diagram):

    def __init__(
        self,
        file_path,
        do_check_errors=True,
        diagram_ref=None,
        inverted_rank_arrows=False,
        parse_terms=False,
        edges=None
    ):

        if not file_path.endswith(".drawio"):
            raise WrongFileFormatError()

        super().__init__(file_path)
        self._diagram_ref = diagram_ref
        self._do_check_errors = do_check_errors
        self._inverted_rank_arrows = inverted_rank_arrows
        self._error_list = None
        self._parse_terms = parse_terms
        self._terms_info = None

        self._relationships = None

        if not self.get_diagram_ref():
            self.set_diagram_ref(DiagramRef())

        self._retrieve_diagram_headers()

        if edges is None:
            edges = self._read_edges()

        self._set_relationships(edges)

        if self._get_parse_terms():
            self._parse_entity_info()

        # retrieve file headers

    def _retrieve_diagram_headers(self):
        tree = ET.parse(self.get_file_path())
        root = tree.getroot()
        try:
            self._modify_date = root.attrib["modified"]
        except KeyError:
            self._modify_date = "July 1, 2024"

        diagram_tag = next(root.iter("diagram"))
        self._name = diagram_tag.attrib["name"]
        self._diagram_id = diagram_tag.attrib["id"]

        graph_model_tag = next(root.iter("mxGraphModel"))
        self.set_grid_dx(graph_model_tag.attrib["dx"])
        self.set_grid_dy(graph_model_tag.attrib["dy"])
        self.set_grid_size(int(graph_model_tag.attrib["gridSize"]))
        self.set_page_width(int(graph_model_tag.attrib["pageWidth"]))
        self.set_page_height(int(graph_model_tag.attrib["pageHeight"]))

    # convert tree based, attribute based data structure into python compatible json-like dictionary
    def _parse_elements(self):
        # parse the xml tree and set the root tag as the root
        tree = ET.parse(self.get_file_path())
        root = tree.getroot()
        root = next(tree.iter("root"))

        element = dict()
        all_cells = [
            child for child in root.findall("mxCell")
        ]  # only add base level cells

        for cell in all_cells:
            cell_attrs = dict()
            cell_attrs.update(cell.attrib)

            # add nested position attributes if any
            nested_attrs = dict()
            for subcell in cell.findall('mxGeometry'):
                nested_attrs.update(subcell.attrib)
            cell_attrs.update(nested_attrs)

            # add style attributes as data attributes
            if "style" in cell.attrib:
                style_terms = dict()
                style_tags = []
                for style_attrib_string in cell.attrib["style"].split(";"):
                    style_term = style_attrib_string.split("=")
                    if len(style_term) > 1:  # for styles with values
                        key, value = style_term
                        style_terms[key] = value
                    elif style_term[0]:  # for style tags or names
                        style_tags.append(style_term[0])
                cell_attrs.update(style_terms)
                cell_attrs["tags"] = style_tags
                del cell_attrs["style"]  # remove style to prevent redundancy

            cell_id = cell.attrib["id"]
            del cell_attrs["id"]  # remove id since it is now used as a key
            element[cell_id] = (
                cell_attrs  # set dictionary of cell key and attribute dictionary
            )

        return element

    # convert draw_io diagram into table of edges
    def _read_edges(self, save_path=None, elements=None, return_entity_ids=False):
        # classify elements in graph as terms or connectors
        if elements is None:
            elements = self._parse_elements()

        terms, rels = set(), set()
        for element, data in elements.items():
            # if the vertex attribute is 1 and edgeLabel is not in tags, it is a term (shape)
            if (
                "vertex" in data
                and data["vertex"] == "1"
                and (
                    "tags" not in data
                    or ("tags" in data and "edgeLabel" not in data["tags"])
                )
            ):
                terms.add(element)
            # if an element has an edgeLabel tag, it is a relationship (connection)
            elif "tags" in data and "edgeLabel" in data["tags"]:
                rel_val = data["value"]
                rel_id = data["parent"]
                elements[rel_id]["value"] = rel_val
                rels.add(rel_id)
            # if an element has value, source and target, it is also a relationship (connection)
            elif "value" in data and "source" in data and "target" in data:
                rel_val = data["value"]
                rel_id = element
                rels.add(rel_id)

        extra_rels = set()
        if self._get_check_errors():
            for element, data in elements.items():
                if "edge" in data and data["edge"] == "1":
                    extra_rels.add(element)

        black_list = set()
        if self._get_check_errors():
            self._check_errors(elements, rels, terms, extra_rels=extra_rels)
            black_list = self._error_list.keys()

        # for identified connectors, extract relationship information
        entries = []
        for rel in rels:

            # if the current relationship id has errors, skip
            if rel in black_list:
                continue

            parent_id = elements[rel]["source"]
            child_id = elements[rel]["target"]
            rel_val = ReadDiagram.clean_term(elements[rel]["value"])

            # if any of the connected terms have errors, skip
            if parent_id in black_list or child_id in black_list:
                continue

            is_rank = self._diagram_ref.is_rank(rel_val)

            # arrow conventions are inverted for rank relationships, flip assignments to conform
            if self.get_inverted_rank_arrows() and is_rank:
                temp = parent_id
                parent_id = child_id
                child_id = temp

            entries.append(
                {
                    "parent_id": parent_id,
                    "child_id": child_id,
                    "rel_id": rel,
                    "parent": ReadDiagram.clean_term(elements[parent_id]["value"]),
                    "child": ReadDiagram.clean_term(elements[child_id]["value"]),
                    "rel": rel_val,
                    "is_rank": is_rank,
                }
            )

        df = pd.DataFrame(entries)

        if save_path:
            df.to_csv(save_path)

        if return_entity_ids:
            return df, terms, rels
        return df

    def _parse_info(self, term, term_parser_titles=None):

        if not term_parser_titles:
            term_parser_titles = self.get_diagram_ref().get_term_parser_titles()

        sep = self.get_diagram_ref().get_term_parser_sep()
        # remove all the html tags in the term
        soup = BeautifulSoup(term, "html.parser")
        term_text = soup.get_text(separator=" ", strip=True)

        # if the name is defined explicitly, parse the term
        # separate string based on keyword presence
        entries = dict()
        term_breaks = [
            term_text.find(f"{key_word}{sep}")
            for key_word in term_parser_titles.values()
        ]  # first find keyword start index
        term_breaks = sorted(
            [term for term in term_breaks if term >= 0]
        )  # sort and remove non-matches
        # use break positions to split the text into a dictionary
        term_break_size = len(term_breaks)
        for i in range(term_break_size):
            start = term_breaks[i]
            end = len(term_text) if i == term_break_size - 1 else term_breaks[i + 1]
            substring = term_text[start:end]
            key, value = substring.split(
                sep, 1
            )  # only use the first occurence from left to right
            entries[key.strip()] = value.strip()

        return term_text, entries

    def _parse_entity_info(self):
        rels = self.get_relationships()
        term_parser_titles = self.get_diagram_ref().get_term_parser_titles()
        term_sep = self.get_diagram_ref().get_shape_param("term_separator")

        term_entries = []
        for row_idx, row in rels.iterrows():
            cols = ["parent", "child", "rel"]
            terms = [row[col] for col in cols]
            parent_term, child_term, parent_prefix = None, None, None

            for col_idx, term in enumerate(terms):
                print(term, cols[col_idx])

                term_text, entries = self._parse_info(term, term_parser_titles)
                term_name = term_text  # set default name from content

                if f"{term_parser_titles['name_title']}:" in term:
                    # rename the row with the cleaned name, set term name to cleaned name
                    term_name = entries[
                        self.get_diagram_ref().get_term_parser_title("name_title")
                    ]
                    rels.at[row_idx, cols[col_idx]] = term_name

                # extract ontology from prefix
                split_term = term_name.split(term_sep, 1)
                if len(split_term) > 1:
                    entries["prefix"], entries["variable"] = split_term
                else:
                    entries["prefix"], entries["variable"] = "ex", split_term[-1]

                # assign term type if term
                entries["is_term"] = (
                    cols[col_idx] == "parent" or cols[col_idx] == "child"
                )

                # save parent term if parent
                if cols[col_idx] == "parent":
                    parent_term = entries["variable"]
                    parent_prefix = entries["prefix"]

                # assign parent if the term is a child
                if cols[col_idx] == "child":
                    entries["parent"] = parent_term
                    entries["parent_prefix"] = parent_prefix
                    child_term = entries["variable"]

                # assign rank if the term is a relationshp
                if cols[col_idx] == "rel":
                    entries["is_data_prop"] = row["is_rank"]
                    entries["subject"] = parent_term
                    entries["object"] = child_term

                # add term as part of the dictionary
                term_entries.append(entries)

        # save all valid terms as dataframe and return
        terms_info_df = pd.DataFrame(term_entries)
        terms_info_df.dropna(how="all", inplace=True)  # only save terms with info

        self._terms_info = terms_info_df

    def _check_errors(self, elements, rels, terms, extra_rels=None):
        # check for errors if present in the diagram file. Assumes draw.io initial fidelity checks pass (file is not edited outside app)
        error_list = dict()
        all_connected_terms = set()

        if extra_rels:
            rels.update(extra_rels)

        for rel_id in rels:
            rel_errors = []
            rel_data = elements[rel_id]
            rel_content = rel_data["value"] if "value" in rel_data else ""
            connected_terms = set()

            if (
                "source" in rel_data
                and "target" in rel_data
                and rel_data["source"] == rel_data["target"]
            ):
                rel_errors.append(CircularEdgeError(rel_id, rel_content))
            elif "source" not in rel_data and "target" not in rel_data:
                rel_errors.append(FloatingEdgeError(rel_id, rel_content))
            elif "source" not in rel_data:
                rel_errors.append(MissingParentEdgeError(rel_id, rel_content))
                connected_terms.add(rel_data["target"])
            elif "target" not in rel_data:
                rel_errors.append(MissingChildEdgeError(rel_id, rel_content))
                connected_terms.add(rel_data["source"])
            else:
                connected_terms.add(rel_data["source"])
                connected_terms.add(rel_data["target"])

            all_connected_terms.update(connected_terms)

            if "value" not in rel_data or not rel_data["value"].strip():
                connected_terms = [
                    (
                        elements[term_id]["value"]
                        if "value" in elements[term_id]
                        and elements[term_id]["value"].strip()
                        else "(blank)"
                    )
                    for term_id in connected_terms
                ]
                rel_errors.append(BlankEdgeLabelError(rel_id, connected_terms))

            edge_error = {"type": "rel", "value": rel_content, "errors": rel_errors}

            if rel_errors:
                error_list[rel_id] = edge_error

        non_connected_terms = terms - all_connected_terms

        for term_id in terms:
            term_data = elements[term_id]
            term_errors = []
            term_content = term_data["value"] if "value" in term_data else ""

            if "value" not in term_data or not term_data["value"].strip():
                term_errors.append(BlankTermLabelError(rel_id))

            if term_id in non_connected_terms:
                term_errors.append(DisconnectedTermError(rel_id, term_content))

            term_error = {"type": "term", "value": term_content, "errors": term_errors}

            if term_errors:
                error_list[term_id] = term_error

        self._error_list = error_list

    def get_relationships(self):
        return self._relationships

    def _set_relationships(self, relationships):
        self._relationships = relationships

    def get_diagram_ref(self):
        return self._diagram_ref

    def set_diagram_ref(self, diagram_ref):
        self._diagram_ref = diagram_ref

    def _get_check_errors(self):
        return self._do_check_errors

    def _set_check_errors(self, do_check_errors):
        self._do_check_errors = do_check_errors

    def get_inverted_rank_arrows(self):
        return self._inverted_rank_arrows

    def _set_inverted_rank_arrows(self, inverted_rank_arrows):
        self._inverted_rank_arrows = inverted_rank_arrows

    def _get_parse_terms(self):
        return self._parse_terms

    def get_terms_info(self):
        return self._terms_info

    def get_errors(self):
        if not self._get_check_errors():
            raise ValueError(
                "Cannot retrieve error list since errors were not checked. Please make sure the argument do_check_errors is set."
            )
        return self._error_list

    def print_errors(self, sep_width=25, print_id_width=25):
        errors = self.get_errors()
        file_path = self.get_file_path()
        file_name, file_ext = path.basename(file_path).split(".")
        # print the list of errors in the console for reference
        print(sep_width * "=")
        print(
            f"Errors for {file_name}.{file_ext}\nLocated in -> {file_path}",
            end=2 * "\n",
        )
        if len(errors) > 0:
            print(f"{'Element ID'.rjust(print_id_width)}\t\tError")
            for elem_id, error_data in errors.items():
                for error in error_data["errors"]:
                    print(f"{elem_id.rjust(print_id_width)}\t->\t{error}")
        else:
            print("No errors to display.")

    @staticmethod
    def clean_term(term):
        soup = BeautifulSoup(term, "html.parser")
        term_text = soup.get_text(separator="", strip=True)
        return term_text
