import re
from collections.abc import Iterable
from functools import reduce
from itertools import chain, groupby

from rdflib import RDF, RDFS, SKOS, Graph, Literal, Namespace, URIRef
from rdflib.namespace import split_uri
from thefuzz import fuzz, process

from cemento.rdf.preprocessing import (
    get_abbrev_term,
    remove_term_names,
)


def substitute_term(
    search_keys: Iterable[str], search_terms: dict[str, URIRef], score_cutoff: int = 80
) -> URIRef:
    best_match, score = max(
        (
            result
            for search_key in search_keys
            if (
                result := process.extractOne(
                    search_key,
                    search_terms.keys(),
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=score_cutoff,
                )
            )
            is not None
        ),
        key=lambda x: x[1] if x is not None else -1,
        default=(None, -1),
    )
    return search_terms[best_match] if best_match else None


def get_term_search_keys(term: str, inv_prefix: dict[URIRef, str]) -> list[str]:
    prefix, abbrev_term = get_abbrev_term(term)
    undo_camel_case_term = " ".join(
        re.findall(r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z][a-z]+|[0-9]+", abbrev_term)
    )
    search_keys = [
        remove_term_names(term),
        f"{prefix}:{abbrev_term}",
        f"{prefix}:{undo_camel_case_term}",
    ]
    return [key.strip() for key in search_keys]


def get_term_search_result(
    term: URIRef,
    inv_prefixes: dict[URIRef | Namespace, str],
    search_terms: dict[str, URIRef],
) -> URIRef:
    ns, abbrev_term = split_uri(term)
    prefix = inv_prefixes[str(ns)]
    search_term = f"{prefix}:{abbrev_term}"
    if search_term in search_terms:
        return search_terms[search_term]
    return None


def add_exact_matches(
    term: URIRef, match_properties: dict[URIRef, URIRef | None], rdf_graph: Graph
) -> Graph:
    # if the term is already imported from somewhere else
    # get the type and label if available and add to the ttl file
    for match_property, value in match_properties.items():
        if value:
            rdf_graph.add((term, match_property, value))

    # add an exact match to the ttl file for easier cross-referencing
    rdf_graph.add((term, SKOS.exactMatch, term))

    return rdf_graph


def get_aliases(rdf_graph: Graph) -> dict[URIRef, Literal]:
    label_tuples = list(
        chain(
            rdf_graph.subject_objects(RDFS.label),
            rdf_graph.subject_objects(SKOS.altLabel),
        )
    )
    sorted(label_tuples, key=lambda x: x[0])
    return {
        subj: [obj for _, obj in objs]
        for subj, objs in groupby(label_tuples, key=lambda x: x[0])
    }


def get_term_types(rdf_graph: Graph) -> dict[URIRef, URIRef]:
    return {subj: obj for subj, pred, obj in rdf_graph if pred == RDF.type}


def combine_graphs(graphs: Iterable[Graph]) -> Graph:
    return reduce(lambda acc, graph: acc + graph, graphs, Graph())
