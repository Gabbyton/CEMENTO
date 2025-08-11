import json
import os
from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path

from rdflib import RDFS, SKOS, Graph, Namespace, URIRef
from rdflib.namespace import split_uri

from cemento.utils.constants import RDFFormat
from cemento.utils.io import get_rdf_format


def get_rdf_file_iter(
    folder_path: str | Path, file_format: str | RDFFormat = None
) -> Iterable[Graph]:
    # TODO: move to constants file
    valid_rdf_file_formats = {e for e in RDFFormat.get_valid_file_extensions()}
    return (
        get_rdf_graph(file_path, file_format=file_format)
        for file in os.scandir(folder_path)
        if (file_path := Path(file.path)).suffix in valid_rdf_file_formats
    )


def get_rdf_graph(file_path: str | Path, file_format: str | RDFFormat) -> Graph | None:
    with read_rdf(file_path, file_format=file_format) as graph:
        return graph


@contextmanager
def read_rdf(file_path: str | Path, file_format: str | RDFFormat) -> Graph:
    rdf_graph = Graph()
    try:
        rdf_graph.parse(
            file_path, format=get_rdf_format(file_path, file_format=file_format)
        )
        yield rdf_graph
    finally:
        rdf_graph.close()


def read_prefixes_from_json(file_path: str) -> dict[str, URIRef]:
    with open(file_path, "r") as f:
        prefixes = json.load(f)
        return prefixes


def get_search_terms_from_defaults(
    default_namespace_prefixes: dict[str, Namespace],
) -> dict[str, URIRef]:
    search_terms = dict()
    for prefix, ns in default_namespace_prefixes.items():
        for term in dir(ns):
            if isinstance(term, URIRef):
                _, name = split_uri(term)
                search_terms[f"{prefix}:{name}"] = term
    return search_terms


def read_prefixes_from_graph(rdf_graph: Graph) -> dict[str, str]:
    return {prefix: str(ns) for prefix, ns in rdf_graph.namespaces()}


def get_search_terms_from_graph(
    rdf_graph: Graph, inv_prefixes: dict[str, str]
) -> dict[str, URIRef]:
    search_terms = dict()
    all_terms = set()
    for subj, pred, obj in rdf_graph:
        all_terms.update([subj, pred, obj])

        # TODO: take comparison set from constnats
        if pred == RDFS.label or pred == SKOS.altLabel:
            ns, _ = split_uri(subj)
            prefix = inv_prefixes[ns]
            search_terms[f"{prefix}:{str(obj)}"] = subj

    for term in all_terms:
        if isinstance(term, URIRef):
            is_literal = False
            try:
                ns, abbrev_term = split_uri(term)
            except ValueError:
                is_literal = not is_literal

            if not is_literal and str(ns) in inv_prefixes:
                prefix = inv_prefixes[str(ns)]
                search_terms[f"{prefix}:{abbrev_term}"] = term

    return search_terms
