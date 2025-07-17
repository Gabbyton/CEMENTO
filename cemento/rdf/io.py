import os
from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path

from networkx import DiGraph
from rdflib import Graph


def get_diagram_terms_iter_with_pred(graph: DiGraph) -> Iterable[str, bool]:
    return (
        (term, term == data["label"])
        for subj, obj, data in graph.edges(data=True)
        for term in (subj, data["label"], obj)
    )


def get_diagram_terms_iter(graph: DiGraph) -> Iterable[str]:
    return (
        term
        for subj, obj, data in graph.edges(data=True)
        for term in (subj, data["label"], obj)
    )


def get_ttl_file_iter(folder_path: str | Path) -> Iterable[Graph]:
    return (
        get_ttl_graph(file_path)
        for file in os.scandir(folder_path)
        if (file_path := Path(file.path)).suffix == ".ttl"
    )


def get_ttl_graph(file_path: str | Path) -> Graph | None:
    with read_ttl(file_path) as graph:
        return graph


@contextmanager
def read_ttl(file_path: str | Path) -> Graph:
    rdf_graph = Graph()
    try:
        rdf_graph.parse(file_path, format="turtle")
        yield rdf_graph
    finally:
        rdf_graph.close()
