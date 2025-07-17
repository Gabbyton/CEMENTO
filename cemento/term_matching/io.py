import json

from rdflib import RDFS, SKOS, Graph, Namespace, URIRef
from rdflib.namespace import split_uri


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

            if not is_literal:
                prefix = inv_prefixes[str(ns)]
                search_terms[f"{prefix}:{abbrev_term}"] = term

    return search_terms
