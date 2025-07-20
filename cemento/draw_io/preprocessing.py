import re
from collections.abc import Iterable

import networkx as nx
from bs4 import BeautifulSoup
from networkx import DiGraph

from cemento.draw_io.constants import Connector, NxEdge, Shape


def remove_literal_id(literal_content: str) -> str:
    # TODO: replace with hashed id pattern
    return re.sub(r"literal_id-(\w+):", "", literal_content)


def replace_term_quotes(graph: DiGraph) -> DiGraph:
    replace_nodes = {term: replace_quotes(term) for term in graph.nodes}
    return nx.relabel_nodes(graph, replace_nodes, copy=True)


def get_terms_with_quotes(graph: DiGraph) -> list[str]:
    return [term for term in graph.nodes if "&quot;" in term]


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
