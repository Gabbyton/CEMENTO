import re
from collections import defaultdict

import tldextract
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import split_uri


def merge_dictionaries(dict_list: list[dict[any, any]]) -> dict[any, any]:
    return {key: value for each_dict in dict_list for key, value in each_dict.items()}


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


def remove_term_names(term: str) -> str:
    match = re.search(r"^([^(]*)", term)
    return match.group(1).strip() if match else term


def get_term_aliases(term: str) -> list[str]:
    match = re.search(r"\(([^)]*)\)", term)
    if match:
        alt_term_string = match.group(1)
        alt_term_string = alt_term_string.split(",")
        return [term.strip() for term in alt_term_string]
    return []


def get_abbrev_term(
    term: str, is_predicate=False, default_prefix="mds"
) -> tuple[str, str]:
    prefix = default_prefix
    abbrev_term = term
    strict_camel_case = False

    term = remove_term_names(term)
    if ":" in term:
        prefix, abbrev_term = term.split(":")

    if is_predicate:
        abbrev_term = abbrev_term.replace("_", " ")
        strict_camel_case = not strict_camel_case

    # if the term is a class, use upper camel case / Pascal case
    abbrev_term = "".join(
        [
            f"{word[0].upper()}{word[1:] if len(word) > 1 else ''}"
            for word in abbrev_term.split()
        ]
    )

    if strict_camel_case and term[0].islower():
        abbrev_term = (
            f"{abbrev_term[0].lower()}{abbrev_term[1:] if len(abbrev_term) > 1 else ''}"
        )

    return prefix, abbrev_term
