import re
from collections import defaultdict
from collections.abc import Callable, Iterable
from itertools import chain, groupby

import networkx as nx
from networkx import DiGraph
from rdflib import OWL, RDF, RDFS, SKOS, BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import split_uri
from thefuzz import fuzz, process

from cemento.rdf.constants import PREDICATES
from cemento.rdf.preprocessing import (
    clean_literal_string,
    get_abbrev_term,
    remove_term_names,
)


def construct_term_uri(
    prefix: str,
    abbrev_term: str,
    prefixes: dict[str, URIRef | Namespace],
) -> URIRef:
    ns_uri = prefixes[prefix]
    return URIRef(f"{ns_uri}{abbrev_term}")


def construct_literal(term: str, lang="en", datatype=None) -> Literal:
    return Literal(clean_literal_string(term), lang=lang, datatype=None)


def get_literal_lang_annotation(literal_term: str, default=None) -> str:
    return res[0] if (res := re.findall(r"@(\w+)", literal_term)) else default


def get_literal_data_type(
    literal_term: str,
    search_terms: dict[str, URIRef],
    score_cutoff=90,
) -> URIRef | None:
    search_key = res[0] if (res := re.findall(r"\^\^(\w+:\w+)", literal_term)) else None
    if search_key:
        datatype = substitute_term(
            [search_key], search_terms, score_cutoff=score_cutoff
        )
        return datatype
    return None


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


def get_doms_ranges(graph: DiGraph) -> dict[URIRef, dict[str, list[URIRef]]]:
    doms_ranges = defaultdict(lambda: defaultdict(list))
    for domain_term, range_term, data in graph.edges(data=True):
        predicate_term = data.get("label", None)
        if predicate_term:
            doms_ranges[predicate_term]["domain"].append(domain_term)
            doms_ranges[predicate_term]["range"].append(range_term)
    return doms_ranges


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


def get_term_value(subj: URIRef, pred: URIRef, ref_rdf_graph: Graph):
    return ref_rdf_graph.value(subj, pred)


def bind_prefixes(rdf_graph: Graph, prefixes: dict[str, URIRef | Namespace]) -> Graph:
    for prefix, ns in prefixes.items():
        rdf_graph.bind(prefix, ns)
    return rdf_graph


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


def add_labels(term: URIRef, labels: list[str], rdf_graph: Graph) -> Graph:
    # assume the first element of the labels is the actual label, others are alt-names
    if labels:
        rdf_graph.add((term, RDFS.label, Literal(labels[0])))
        if len(labels) > 1:
            for label in labels[1:]:
                rdf_graph.add((term, SKOS.altLabel, Literal(label)))
    return rdf_graph


def add_domains_ranges(
    term: URIRef,
    domains_ranges: dict[str, list[URIRef]],
    rdf_graph: Graph,
) -> Graph:
    predicate_domain = domains_ranges["domain"]
    predicate_range = domains_ranges["range"]

    for dom_or_range_term, term_dom_range in {
        RDFS.domain: predicate_domain,
        RDFS.range: predicate_range,
    }.items():
        if term_dom_range:
            # if there are more than one term, save the domain or range as a collection
            if len(term_dom_range) > 1:
                collection_node = BNode()
                Collection(rdf_graph, collection_node, term_dom_range)
                # create class that points to the collection
                collection_class = BNode()
                rdf_graph.add((collection_class, RDF.type, OWL.Class))
                # connect them all together
                # TODO: assume union for now but fix later
                rdf_graph.add((collection_class, OWL.unionOf, collection_node))
                rdf_graph.add((term, dom_or_range_term, collection_class))
            else:
                # if there is only one term, use that term directly
                rdf_graph.add((term, dom_or_range_term, term_dom_range[0]))


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


def get_instances(
    rdf_graph: Graph, default_terms: set[URIRef], term_types: dict[URIRef, URIRef]
) -> set[URIRef]:
    return {
        obj
        for subj, pred, obj in rdf_graph
        if pred == RDF.type
        and obj not in default_terms
        and term_types[obj] == OWL.Class
    }


def get_classes(
    rdf_graph: Graph, default_terms: set[URIRef], term_types: dict[URIRef, URIRef]
) -> set[URIRef]:
    instance_superclasses = {
        subj
        for subj, pred, obj in rdf_graph
        if pred == RDF.type
        and obj not in default_terms
        and term_types[subj] == OWL.Class
    }
    subclass_terms = {
        term
        for subj, pred, obj in rdf_graph
        if pred == RDFS.subClassOf
        for term in (subj, obj)
    }
    return instance_superclasses | subclass_terms


def get_predicates(rdf_graph: Graph, default_terms: set[URIRef]) -> set[URIRef]:
    return {term for prop in PREDICATES for term in rdf_graph.subjects(RDF.type, prop)}


def get_graph_relabel_mapping(
    terms: URIRef,
    all_classes: set[URIRef],
    all_instances: set[URIRef],
    aliases: dict[URIRef, Literal],
    inv_prefix: dict[URIRef | Namespace, str],
) -> dict[URIRef, str]:
    rename_mapping = dict()
    for term in terms:
        ns, abbrev_term = split_uri(term)
        prefix = inv_prefix[ns]
        new_name = f"{prefix}:{abbrev_term}"
        if term in aliases and aliases[term]:
            if term in all_classes or term in all_instances:
                new_name += f" ({','.join(aliases[term])})"
            else:
                new_name = f"{prefix}:{aliases[term][0]}"
        rename_mapping[term] = new_name
    return rename_mapping


def get_graph(
    rdf_graph: Graph, all_predicates: set[URIRef], default_terms: set[URIRef]
) -> DiGraph:
    graph = DiGraph()
    for subj, pred, obj in rdf_graph:
        if (
            pred in all_predicates
            and subj not in default_terms
            and obj not in default_terms
        ):
            is_rank = pred == RDF.type or pred == RDFS.subClassOf
            graph.add_edge(obj, subj, label=pred, is_rank=is_rank)
    return graph


def rename_edges(graph: DiGraph, rename_mapping: dict[URIRef, str]) -> DiGraph:
    edge_rename_mapping = dict()
    graph = graph.copy()
    for subj, obj, data in graph.edges(data=True):
        pred = data["label"]
        new_edge_label = rename_mapping[pred]
        edge_rename_mapping[(subj, obj)] = {"label": new_edge_label}
    nx.set_edge_attributes(graph, edge_rename_mapping)
    return graph
