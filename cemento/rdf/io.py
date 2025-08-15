from collections.abc import Iterable
from itertools import chain
from pathlib import Path

import pandas as pd
from more_itertools import unique_everseen
from networkx import DiGraph
from rdflib import URIRef

from cemento.utils.utils import fst


def get_diagram_terms_iter_with_pred(graph: DiGraph) -> Iterable[str, bool]:
    diagram_terms_from_edges = (
        (term, term == data["label"])
        for subj, obj, data in graph.edges(data=True)
        for term in (subj, data["label"], obj)
        if term
    )
    diagram_terms_from_nodes = ((node, False) for node in graph.nodes)
    return unique_everseen(
        chain(diagram_terms_from_edges, diagram_terms_from_nodes), key=lambda x: fst(x)
    )


def get_diagram_terms_iter(graph: DiGraph) -> Iterable[str]:
    diagram_terms_from_edges = (
        term
        for subj, obj, data in graph.edges(data=True)
        for term in (subj, data["label"], obj)
        if term
    )
    return unique_everseen(chain(diagram_terms_from_edges, graph.nodes))


def save_substitute_log(
    substitution_results: dict[str, tuple[URIRef, Iterable[str], Iterable[str]]],
    log_substitution_path: str | Path,
) -> None:
    log_entries = [
        (original_term, search_key, term, score, matched_term)
        for original_term, (
            matched_term,
            search_keys,
            matches,
        ) in substitution_results.items()
        for (search_key, (term, score)) in zip(search_keys, matches, strict=False)
    ]
    df = pd.DataFrame(
        log_entries,
        columns=[
            "original_term",
            "search_key",
            "search_result",
            "score",
            "matched_term",
        ],
    )
    df.to_csv(log_substitution_path)
