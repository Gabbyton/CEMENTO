from rdflib import Namespace, URIRef
from rdflib.namespace import split_uri

from cemento.term_matching.transforms import get_term_search_result


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
    # assume all default namespaces terms are resolvable by split_uri
    try:
        ns, abbrev_term = split_uri(term)
    except ValueError:
        return False
    prefix = inv_prefixes[str(ns)]
    return prefix not in default_namespace_prefixes
