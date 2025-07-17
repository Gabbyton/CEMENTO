import re
from collections import defaultdict
from collections.abc import Iterable
from functools import partial, reduce
from itertools import chain, groupby
from pathlib import Path

import tldextract
from rdflib import RDF, RDFS, SKOS, Graph, Literal, Namespace, URIRef
from rdflib.namespace import split_uri
from thefuzz import fuzz, process

from cemento.term_matching.constants import get_default_namespace_prefixes
from cemento.term_matching.io import (
    get_search_terms_from_defaults,
    get_search_terms_from_graph,
    get_ttl_file_iter,
    read_prefixes_from_graph,
    read_prefixes_from_json,
)
from cemento.term_matching.preprocessing import merge_dictionaries
from cemento.utils.utils import get_abbrev_term, remove_term_names


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


def generate_residual_prefixes(
    rdf_graph: Graph, inv_prefixes: dict[Namespace | URIRef, str]
):
    new_prefixes = defaultdict(list)
    new_prefix_namespaces = set()
    for subj, pred, obj in rdf_graph:
        for term in [subj, pred, obj]:
            if isinstance(term, URIRef):
                try:
                    ns, abbrev = split_uri(term)
                except ValueError:
                    ns = term
                if ns not in inv_prefixes:
                    new_prefix_namespaces.add(str(ns))
    gns_idx = 0
    for ns in new_prefix_namespaces:
        url_extraction = tldextract.extract(ns)
        new_prefix = res[-1] if (res := re.findall(r"\w+", ns)) else ""
        if url_extraction.suffix and new_prefix in url_extraction.suffix.split("."):
            new_prefix = url_extraction.domain
        new_prefix = re.sub(r"[^a-zA-Z0-9]", "", new_prefix)
        if not new_prefix or new_prefix.isdigit():
            new_prefix = f"gns{gns_idx}"
            gns_idx += 1
        new_prefixes[new_prefix].append(ns)

    return_prefixes = dict()
    for prefix, namespaces in new_prefixes.items():
        if len(namespaces) > 1:
            for idx, ns in enumerate(namespaces):
                return_prefixes[f"{prefix}{idx+1}"] = ns
        else:
            return_prefixes[prefix] = namespaces[0]

    return return_prefixes


def get_prefixes(
    prefixes_path: str | Path, onto_ref_folder: str | Path
) -> tuple[dict[str, URIRef | Namespace], dict[URIRef | Namespace, str]]:
    prefixes = dict()
    if prefixes_path:
        prefixes = read_prefixes_from_json(prefixes_path)

    default_namespace_prefixes = get_default_namespace_prefixes()
    prefixes.update(default_namespace_prefixes)

    if onto_ref_folder:
        file_prefixes = map(
            read_prefixes_from_graph, get_ttl_file_iter(onto_ref_folder)
        )
        prefixes |= merge_dictionaries(file_prefixes)
        inv_prefixes = {value: key for key, value in prefixes.items()}

        residual_file_prefixes = map(
            partial(generate_residual_prefixes, inv_prefixes=inv_prefixes),
            get_ttl_file_iter(onto_ref_folder),
        )
        residual_file_prefixes = {
            key: value
            for residual_prefixes in residual_file_prefixes
            for key, value in residual_prefixes.items()
        }
        prefixes.update(residual_file_prefixes)
        inv_prefixes = {value: key for key, value in prefixes.items()}

    return prefixes, inv_prefixes


def get_search_terms(inv_prefixes: dict[URIRef, str], onto_ref_folder: str | Path):
    search_terms = get_search_terms_from_defaults(get_default_namespace_prefixes())

    if onto_ref_folder:
        file_search_terms = map(
            partial(get_search_terms_from_graph, inv_prefixes=inv_prefixes),
            get_ttl_file_iter(onto_ref_folder),
        )
        search_terms |= merge_dictionaries(file_search_terms)

    return search_terms
