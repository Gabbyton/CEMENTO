from collections.abc import Iterable

import networkx as nx
from bs4 import BeautifulSoup
from networkx import DiGraph

from cemento.draw_io.constants import NxEdge


def replace_term_quotes(graph: DiGraph) -> DiGraph:
    replace_nodes = {term: replace_quotes(term) for term in graph.nodes}
    return nx.relabel_nodes(graph, replace_nodes, copy=True)


def remove_predicate_quotes(edges: Iterable[NxEdge]) -> Iterable[NxEdge]:
    return map(lambda edge: (edge.subj, edge.obj, remove_quotes(edge.pred)), edges)


def clean_term(term: str) -> str:
    soup = BeautifulSoup(term, "html.parser")
    term_text = soup.get_text(separator="", strip=True)
    return term_text


def replace_quotes(input_str: str) -> str:
    return input_str.replace('"', "&quot;")


def remove_html_quote(input_str: str) -> str:
    return input_str.replace("&quot;", "")


def remove_quotes(input_str: str) -> str:
    return remove_html_quote(input_str.replace('"', "").strip())
