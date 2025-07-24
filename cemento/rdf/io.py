from collections.abc import Iterable
from pathlib import Path

import pandas as pd
from networkx import DiGraph
from rdflib import URIRef


def get_diagram_terms_iter_with_pred(graph: DiGraph) -> Iterable[str, bool]:
    return (
        (term, term == data["label"])
        for subj, obj, data in graph.edges(data=True)
        for term in (subj, data["label"], obj)
        if term
    )


def get_diagram_terms_iter(graph: DiGraph) -> Iterable[str]:
    return (
        term
        for subj, obj, data in graph.edges(data=True)
        for term in (subj, data["label"], obj)
        if term
    )


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
