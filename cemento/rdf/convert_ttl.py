import re
from collections import defaultdict
from collections.abc import Callable, Iterable
from functools import partial

import networkx as nx
import rdflib
from networkx import DiGraph
from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import split_uri
from thefuzz import fuzz, process

from cemento.draw_io.read_diagram import ReadDiagram
from cemento.rdf.io import (
    get_search_terms_from_defaults,
    get_search_terms_from_graph,
    iter_diagram_terms,
    iterate_ttl_graphs,
    read_prefixes_from_graph,
    read_prefixes_from_json,
)

INPUT_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/recipe.drawio"
ONTO_FOLDER = "/Users/gabriel/dev/sdle/CEMENTO/data"
PREFIXES_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/prefixes.json"
TTL_OUTPUT_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/recipe.ttl"
DRAWIO_OUTPUT_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/recipe-redraw.drawio"


def merge_dictionaries(dict_list: list[dict[any, any]]) -> dict[any, any]:
    return {key: value for each_dict in dict_list for key, value in each_dict.items()}


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


def construct_term_uri(
    prefix: str,
    abbrev_term: str,
    prefixes: dict[str, URIRef | Namespace],
) -> URIRef:
    ns_uri = prefixes[prefix]
    return rdflib.URIRef(f"{ns_uri}{abbrev_term}")


def substitute_term(
    search_keys: Iterable[str], search_terms: dict[str, URIRef]
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
                    score_cutoff=75,
                )
            )
            is not None
        ),
        key=lambda x: x[1] if x is not None else -1,
        default=(None, -1),
    )
    return search_terms[best_match] if best_match else None


def bind_prefixes(rdf_graph: Graph, prefixes: dict[str, URIRef | Namespace]) -> Graph:
    for prefix, ns in prefixes.items():
        rdf_graph.bind(prefix, ns)
    return rdf_graph


def get_class_terms(graph: DiGraph) -> set[URIRef]:
    class_terms = set()
    for subj, obj, data in graph.edges(data=True):
        predicate = data["label"]

        if predicate == RDFS.subClassOf:
            # we assume terms between RDFS.subClassOf is a class
            class_terms.update([subj, obj])

        if predicate == RDF.type:
            # we assume the object of an RDF.type is also a class
            class_terms.add(obj)

    return class_terms


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


def term_in_search_results(
    term: URIRef,
    inv_prefixes: dict[URIRef | Namespace, str],
    search_terms: dict[str, URIRef],
    invert=False,
) -> URIRef:
    eval_value = get_term_search_result(term, inv_prefixes, search_terms) is not None
    if invert:
        eval_value = not eval_value
    return eval_value


def term_not_in_default_namespace(
    term: URIRef,
    inv_prefixes: dict[URIRef | Namespace, str],
    default_namespace_prefixes: dict[str, Namespace],
    invert=False,
) -> bool:
    ns, abbrev_term = split_uri(term)
    prefix = inv_prefixes[str(ns)]
    eval_value = prefix not in default_namespace_prefixes
    if invert:
        eval_value = not eval_value
    return eval_value


def iter_graph_terms(
    graph_terms: set[URIRef],
    term_function: Callable[[URIRef], None],
    filter_functions: Iterable[Callable[..., bool]] = None,
    invert_filter=False,
) -> list[any]:
    results = []
    for term in graph_terms:
        eval_value = True
        if filter_functions:
            eval_value = all(
                [filter_function(term) for filter_function in filter_functions]
            )
            if invert_filter:
                eval_value = not eval_value

        if eval_value:
            results.append(term_function(term))
    return results


def add_domains_ranges(term: URIRef):
    predicate_domain = defaultdict(list)
    predicate_range = defaultdict(list)
    for domain_term, range_term, data in graph.edges(data=True):
        predicate_term = data["label"]
        predicate_domain[predicate_term].append(domain_term)
        predicate_range[predicate_term].append(range_term)

    for dom_or_range_term, term_dom_range in {
        RDFS.domain: predicate_domain[term],
        RDFS.range: predicate_range[term],
    }.items():
        if term_dom_range:
            # if there are more than one term, save the domain or range as a collection
            if len(term_dom_range) > 1:
                collection_node = rdflib.BNode()
                Collection(rdf_graph, collection_node, term_dom_range)
                # create class that points to the collection
                collection_class = rdflib.BNode()
                rdf_graph.add((collection_class, RDF.type, OWL.Class))
                # connect them all together
                # TODO: assume union for now but fix later
                rdf_graph.add((collection_class, OWL.unionOf, collection_node))
                rdf_graph.add((term, dom_or_range_term, collection_class))
            else:
                # if there is only one term, use that term directly
                rdf_graph.add((term, dom_or_range_term, term_dom_range[0]))


def get_term_value(subj: URIRef, pred: URIRef, ref_rdf_graph: Graph):
    return ref_rdf_graph.value(subj, pred)


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


def add_labels(term: URIRef, labels: list[str], rdf_graph: Graph) -> Graph:
    # assume the first element of the labels is the actual label, others are alt-names
    if labels:
        rdf_graph.add((term, RDFS.label, Literal(labels[0])))
        if len(labels) > 1:
            for label in labels[1:]:
                rdf_graph.add((term, SKOS.altLabel, Literal(label)))
    return rdf_graph


if __name__ == "__main__":
    default_namespaces = [RDF, RDFS, OWL, DCTERMS, SKOS]
    default_namespace_prefixes = ["rdf", "rdfs", "owl", "dcterms", "skos"]

    prefixes = read_prefixes_from_json(PREFIXES_PATH)

    default_namespace_prefixes = {
        prefix: ns for prefix, ns in zip(default_namespace_prefixes, default_namespaces)
    }
    prefixes.update(default_namespace_prefixes)
    file_prefixes = iterate_ttl_graphs(ONTO_FOLDER, read_prefixes_from_graph)
    prefixes |= merge_dictionaries(file_prefixes)

    inv_prefixes = {value: key for key, value in prefixes.items()}

    search_terms = get_search_terms_from_defaults(default_namespace_prefixes)
    file_search_terms = iterate_ttl_graphs(
        ONTO_FOLDER, partial(get_search_terms_from_graph, inv_prefixes=inv_prefixes)
    )
    search_terms |= merge_dictionaries(file_search_terms)

    # read the diagram and retrieve the relationship triples as a dataframe
    diagram = ReadDiagram(INPUT_PATH, inverted_rank_arrows=True)
    rels = diagram.get_relationships()
    rels.to_csv("sample.csv")

    aliases = {
        term: aliases
        for term, aliases in iter_diagram_terms(
            rels, lambda term: (term, get_term_aliases(term))
        )
    }

    constructed_terms = {
        term: term_uri_ref
        for term, term_uri_ref in iter_diagram_terms(
            rels,
            lambda term, is_predicate: (
                term,
                construct_term_uri(
                    *get_abbrev_term(term, is_predicate=is_predicate), prefixes=prefixes
                ),
            ),
        )
    }
    search_keys = {
        term: search_key
        for term, search_key in iter_diagram_terms(
            rels, lambda term: (term, get_term_search_keys(term, inv_prefixes))
        )
    }
    substitution_results = {
        term: substituted_value
        for term, substituted_value in iter_diagram_terms(
            rels,
            lambda term: (term, substitute_term(search_keys[term], search_terms)),
        )
        if substituted_value is not None
    }

    inv_constructed_terms = {value: key for key, value in constructed_terms.items()}

    constructed_terms.update(substitution_results)

    graph = nx.DiGraph()
    for _, row in rels.iterrows():
        subj, obj, pred = row["parent"], row["child"], row["rel"]
        subj, obj, pred = tuple(constructed_terms[key] for key in (subj, obj, pred))
        graph.add_edge(subj, obj, label=pred)

    class_terms = get_class_terms(graph)
    predicate_terms = {data["label"] for _, _, data in graph.edges(data=True)}
    class_terms -= predicate_terms
    all_terms = graph.nodes() | predicate_terms

    # # create the rdf graph to store the ttl output
    rdf_graph = rdflib.Graph()

    # bind prefixes to namespaces for the rdf graph
    rdf_graph = bind_prefixes(rdf_graph, prefixes)

    # add all of the class terms as a type
    for term in class_terms:
        rdf_graph.add((term, RDF.type, OWL.Class))

    # if the term is a predicate and is not part of the default namespaces, add an object property type to the ttl file
    for term in predicate_terms:
        # TODO: Assume all predicates are object properties for now, change later
        if term_not_in_default_namespace(
            term, inv_prefixes, default_namespace_prefixes
        ):
            rdf_graph.add((term, RDF.type, OWL.ObjectProperty))

    exact_match_properties = [RDF.value, RDFS.label]
    results = {
        term: {prop: value}
        for prop in exact_match_properties
        for result in iterate_ttl_graphs(
            ONTO_FOLDER,
            lambda rdf_graph, prop=prop: iter_graph_terms(
                all_terms,
                lambda graph_term: (
                    graph_term,
                    get_term_value(subj=graph_term, pred=prop, ref_rdf_graph=rdf_graph),
                ),
            ),
        )
        for term, value in result
    }

    term_in_search_results_filter = partial(
        term_in_search_results, inv_prefixes=inv_prefixes, search_terms=search_terms
    )
    term_not_in_default_namespace_filter = partial(
        term_not_in_default_namespace,
        inv_prefixes=inv_prefixes,
        default_namespace_prefixes=default_namespace_prefixes,
    )

    iter_graph_terms(
        all_terms,
        lambda graph_term: add_exact_matches(
            graph_term, match_properties=results[graph_term], rdf_graph=rdf_graph
        ),
        [term_in_search_results_filter, term_not_in_default_namespace_filter],
    )
    iter_graph_terms(
        all_terms,
        lambda graph_term: add_labels(
            term=graph_term,
            labels=aliases[inv_constructed_terms[graph_term]],
            rdf_graph=rdf_graph,
        ),
        [
            term_not_in_default_namespace_filter,
            partial(
                term_in_search_results,
                inv_prefixes=inv_prefixes,
                search_terms=search_terms,
                invert=True,
            ),
        ],
    )

    # now add the triples from the drawio diagram
    for domain_term, range_term, data in graph.edges(data=True):
        predicate_term = data["label"]
        rdf_graph.add((domain_term, predicate_term, range_term))
    # serialize the output as a turtle file
    rdf_graph.serialize(TTL_OUTPUT_PATH)
