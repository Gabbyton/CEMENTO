import pandas as pd


class WriteArray:

    def __init__(self, read_diagram):

        if not read_diagram._parse_terms:
            raise AttributeError(
                "Cannot write output if terms are not parsed. Please set parse_terms arg to True in ReadDiagram."
            )

        self._diagram = read_diagram
        self._rels = read_diagram.get_relationships()
        self._terms_info = read_diagram.get_terms_info()

        self._var_array = None
        self._rel_array = None

        self._set_var_array()
        self._set_rel_array()

    def _prepare_terms(self, titles=None, get_terms=True):
        if not titles:
            titles = self.get_diagram().get_diagram_ref().get_term_parser_titles()

        info_df = self.get_terms_info().copy()
        info_df = (
            info_df[info_df["is_term"]] if get_terms else info_df[~info_df["is_term"]]
        )

        # ensure all the title columns are made if not in the dataframe already
        for title in titles.values():
            if title not in info_df.columns:
                info_df[title] = pd.Series([])

        return info_df

    def _set_var_array(self):
        titles = self.get_diagram().get_diagram_ref().get_term_parser_titles()
        term_info = self._prepare_terms(titles=titles, get_terms=True)

        export_colname_map = {
            "variable": "VariableName",
            "prefix": "WhichOntologyItBelongsTo",
            "parent": "ParentVariable",
            "parent_prefix": "WhichOntologyParentBelongsTo",
            titles["definition_title"]: "Definition",
            titles["alt_names_title"]: "AlternativeNames",
            titles["unit_title"]: "Unit",
            titles["axioms_title"]: "LogicalAxioms",
            titles["unit_onto_title"]: "WhichOntoUnitBelongsTo",
        }
        remove_cols = [
            col for col in term_info.columns if col not in export_colname_map.keys()
        ]
        term_info.drop(remove_cols, axis=1, inplace=True)
        term_info.rename(columns=export_colname_map, inplace=True)

        self._var_array = term_info

    def _set_rel_array(self):
        titles = self.get_diagram().get_diagram_ref().get_term_parser_titles()
        rel_info = self._prepare_terms(titles=titles, get_terms=False)

        export_colname_map = {
            "variable": "RelationshipName",
            "prefix": "WhichOntologyItBelongsTo",
            "subject": "Subject",
            "object": "Object",
            "is_data_prop": "IsDataProperty",
            titles["definition_title"]: "Definition",
            titles["alt_names_title"]: "AlternativeNames",
            titles["axioms_title"]: "LogicalAxioms",
            titles["data_type_title"]: "DataType",
        }
        remove_cols = [
            col for col in rel_info.columns if col not in export_colname_map.keys()
        ]
        rel_info.drop(remove_cols, axis=1, inplace=True)
        rel_info.rename(columns=export_colname_map, inplace=True)

        self._rel_array = rel_info

    def get_diagram(self):
        return self._diagram

    def get_rels(self):
        return self._rels

    def get_terms_info(self):
        return self._terms_info

    def get_var_array(self):
        return self._var_array

    def get_rel_array(self):
        return self._rel_array
