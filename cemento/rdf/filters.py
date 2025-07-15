from rdflib import Namespace, URIRef
from rdflib.namespace import split_uri

from cemento.rdf.transforms import get_term_search_result


def term_in_search_results(
    term: URIRef,
    inv_prefixes: dict[URIRef | Namespace, str],
    search_terms: dict[str, URIRef],
) -> URIRef:
    return get_term_search_result(term, inv_prefixes, search_terms) is not None


def term_not_in_default_namespace(
    term: URIRef,
    inv_prefixes: dict[URIRef | Namespace, str],
    default_namespace_prefixes: dict[str, Namespace],
) -> bool:
    ns, abbrev_term = split_uri(term)
    prefix = inv_prefixes[str(ns)]
    return prefix not in default_namespace_prefixes
