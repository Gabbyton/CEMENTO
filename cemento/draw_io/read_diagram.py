from enum import Enum
from pathlib import Path

import networkx as nx
from bs4 import BeautifulSoup
from defusedxml import ElementTree as ET
from networkx import DiGraph
from thefuzz import process


class DiagramKey(Enum):
    TERM_ID = "term_id"
    LABEL = "label"


def get_diagram_headers(file_path: str | Path) -> dict[str, str]:
    # retrieve diagram headers
    tree = ET.parse(file_path)
    root = tree.getroot()
    graph_model_tag = next(root.iter("mxGraphModel"))
    diagram_tag = next(root.iter("diagram"))
    diagram_headers = {
        "modify_date": (
            root.attrib["modified"] if "modified" in root.attrib else "July 1, 2024"
        ),
        "diagram_name": diagram_tag.attrib["name"],
        "diagram_id": diagram_tag.attrib["id"],
        "grid_dx": graph_model_tag.attrib["dx"] if "dx" in graph_model_tag else 0,
        "grid_dy": graph_model_tag.attrib["dy"] if "dy" in graph_model_tag else 0,
        "grid_size": int(graph_model_tag.attrib["gridSize"]),
        "page_width": int(graph_model_tag.attrib["pageWidth"]),
        "page_height": int(graph_model_tag.attrib["pageHeight"]),
    }

    return diagram_headers


def parse_elements(file_path: str | Path) -> dict[str, dict[str, any]]:
    # parse elements
    tree = ET.parse(file_path)
    root = tree.getroot()
    root = next(tree.iter("root"))

    elements = dict()
    all_cells = [child for child in root.findall("mxCell")]  # only add base level cells

    for cell in all_cells:
        cell_attrs = dict()
        cell_attrs.update(cell.attrib)

        # add nested position attributes if any
        nested_attrs = dict()
        for subcell in cell.findall("mxGeometry"):
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
        elements[cell_id] = (
            cell_attrs  # set dictionary of cell key and attribute dictionary
        )

    return elements


def extract_elements(
    elements: dict[str, dict[str, any]],
) -> tuple[set[dict[str, any], set[str]]]:
    # read edges
    term_ids, rel_ids = set(), set()
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
            term_ids.add(element)
        # if an element has an edgeLabel tag, it is a relationship (connection)
        elif "tags" in data and "edgeLabel" in data["tags"]:
            rel_val = data["value"]
            rel_id = data["parent"]
            elements[rel_id]["value"] = rel_val
            rel_ids.add(rel_id)
        # if an element has value, source and target, it is also a relationship (connection)
        elif "value" in data and "source" in data and "target" in data:
            rel_val = data["value"]
            rel_id = element
            rel_ids.add(rel_id)
    return term_ids, rel_ids


def clean_term(term: str) -> str:
    soup = BeautifulSoup(term, "html.parser")
    term_text = soup.get_text(separator="", strip=True)
    return term_text


def generate_graph(
    elements: dict[str, dict[str, any]],
    term_ids: set[str],
    relationship_ids: set[str],
    rank_terms: set[str],
    inverted_rank_arrow: bool = False,
) -> DiGraph:
    # for identified connectors, extract relationship information
    graph = nx.DiGraph()
    # add all terms
    for term_id in term_ids:
        term = elements[term_id]["value"]
        graph.add_node(term_id, term_id=term_id, label=clean_term(term))

    # add all relationships
    for rel_id in relationship_ids:
        subj_id = elements[rel_id]["source"]
        obj_id = elements[rel_id]["target"]
        pred = clean_term(elements[rel_id]["value"])

        matched_rank_pred, score = process.extractOne(
            pred.lower(), [rank_term.lower() for rank_term in rank_terms]
        )
        is_rank = score > 85
        pred = matched_rank_pred if is_rank else pred

        # arrow conventions are inverted for rank relationships, flip assignments to conform
        if inverted_rank_arrow and is_rank:
            temp = subj_id
            subj_id = obj_id
            obj_id = temp

        graph.add_edge(
            subj_id,
            obj_id,
            label=pred,
            pred_id=rel_id,
            is_rank=is_rank,
            is_predicate=True,
        )

    return graph


def relabel_graph_nodes(
    graph: DiGraph, new_attr_label=DiagramKey.TERM_ID.value
) -> DiGraph:
    node_info = nx.get_node_attributes(graph, new_attr_label)
    relabel_mapping = {
        current_node_label: node_info[current_node_label]
        for current_node_label in graph.nodes
    }
    return nx.relabel_nodes(graph, relabel_mapping)


def read_drawio(
    input_path: str | Path,
    relabel_key: DiagramKey = DiagramKey.LABEL,
    inverted_rank_arrow: bool = False,
) -> DiGraph:
    elements = parse_elements(input_path)
    term_ids, rel_ids = extract_elements(elements)
    rank_terms = ["rdfs:subClassOf", "rdf:type"]
    graph = generate_graph(
        elements, term_ids, rel_ids, rank_terms, inverted_rank_arrow=inverted_rank_arrow
    )
    graph = relabel_graph_nodes(graph, new_attr_label=relabel_key.value)
    return graph
