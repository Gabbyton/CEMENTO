from collections.abc import Iterable

from networkx import DiGraph


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
