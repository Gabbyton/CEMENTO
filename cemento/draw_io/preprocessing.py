import re
from collections.abc import Iterable

import networkx as nx
from bs4 import BeautifulSoup
from networkx import DiGraph

from cemento.draw_io.constants import (
    BlankEdgeLabelError,
    BlankTermLabelError,
    CircularEdgeError,
    Connector,
    DisconnectedTermError,
    FloatingEdgeError,
    MissingChildEdgeError,
    MissingParentEdgeError,
    NxEdge,
    Shape,
)
from cemento.utils.utils import fst, snd


def remove_literal_id(literal_content: str) -> str:
    # TODO: replace with hashed id pattern
    return re.sub(r"literal_id-(\w+):", "", literal_content)


def replace_term_quotes(graph: DiGraph) -> DiGraph:
    replace_nodes = {term: replace_quotes(term) for term in graph.nodes}
    return nx.relabel_nodes(graph, replace_nodes, copy=True)


def remove_predicate_quotes(edges: Iterable[NxEdge]) -> Iterable[NxEdge]:
    return map(
        lambda edge: (
            (edge.subj, edge.obj, remove_quotes(edge.pred)) if edge.pred else None
        ),
        edges,
    )


def replace_shape_html_quotes(shape: Shape) -> Shape:
    # TODO: implement immutable object copy
    shape.shape_content = replace_quotes(shape.shape_content)
    return shape


def remove_literal_shape_id(shape: Shape) -> Shape:
    # TODO: implement immutable object copy
    shape.shape_content = remove_literal_id(shape.shape_content)
    return shape


def remove_literal_connector_id(connector: Connector) -> Connector:
    connector.connector_val = remove_literal_id(connector.connector_val)
    return connector


def clean_term(term: str) -> str:
    soup = BeautifulSoup(term, "html.parser")
    term_text = soup.get_text(separator="", strip=True)
    return term_text


def replace_quotes(input_str: str) -> str:
    return input_str.replace('"', "&quot;")


def remove_html_quote(input_str: str) -> str:
    return input_str.replace("&quot;", "")


def remove_quotes(input_str: str) -> str:
    if not input_str or not isinstance(input_str, str):
        return input_str
    return remove_html_quote(input_str.replace('"', "").strip())


def find_edge_errors_diagram_content(
    elements, serious_only: bool = False
) -> list[tuple[str, BaseException]]:
    edges = {
        key: value
        for key, value in elements.items()
        if "edge" in value and value["edge"] == "1"
    }
    errors = []
    for edge_id, edge_attr in edges.items():

        connected_terms = {
            edge_attr.get("source", None),
            edge_attr.get("target", None),
        } - {None, ""}

        edge_content = edge_attr.get("value", None)

        if "value" not in edge_attr or not edge_attr["value"]:
            errors.append((edge_id, BlankEdgeLabelError(edge_id, connected_terms)))

        if all(
            [
                "source" not in edge_attr or not edge_attr["source"],
                "target" not in edge_attr or not edge_attr["target"],
            ]
        ):
            errors.append((edge_id, FloatingEdgeError(edge_id, edge_content)))
            continue

        if "source" not in edge_attr or not edge_attr["source"]:
            errors.append((edge_id, MissingParentEdgeError(edge_id, edge_content)))
            continue

        if "target" not in edge_attr or not edge_attr["target"]:
            errors.append((edge_id, MissingChildEdgeError(edge_id, edge_content)))
            continue

        if (
            "target" in edge_attr
            and "source" in edge_attr
            and edge_attr["target"] == edge_attr["source"]
        ):
            errors.append((edge_id, CircularEdgeError(edge_id, edge_content)))

    if serious_only:
        # hide the errors related to circular edges (false positive bug with draw.io)
        circular_edge_errors = filter(
            lambda error: isinstance(snd(error), CircularEdgeError), errors
        )
        non_affected_ids = {id for id, error in circular_edge_errors}
        errors = list(filter(lambda error: fst(error) not in non_affected_ids, errors))

    return errors


def find_shape_errors_diagram_content(elements, term_ids, rel_ids):
    connected_terms = {
        term
        for rel_id in rel_ids
        for term in (
            elements[rel_id].get("source", None),
            elements[rel_id].get("target", None),
        )
    }
    connected_terms -= {None, ""}

    errors = []
    for term_id in term_ids:
        term = elements[term_id]
        if term_id not in connected_terms:
            errors.append((term_id, DisconnectedTermError(term_id, term["value"])))

        if "value" not in term or not term["value"]:
            errors.append((term_id, BlankTermLabelError(term_id)))
    return errors


def find_errors_diagram_content(
    elements: dict[str, dict[str, any]],
    term_ids: set[str],
    rel_ids: set[str],
    serious_only: bool = False,
) -> list[tuple[str, BaseException]]:
    return find_shape_errors_diagram_content(
        elements, term_ids, rel_ids
    ) + find_edge_errors_diagram_content(elements, serious_only=serious_only)
