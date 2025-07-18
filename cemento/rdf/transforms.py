import re
from collections.abc import Iterable
from functools import reduce

import networkx as nx
from networkx import DiGraph
from rdflib import OWL, RDF, RDFS, SKOS, BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import split_uri

from cemento.rdf.constants import PREDICATES
from cemento.rdf.preprocessing import clean_literal_string
from cemento.term_matching.transforms import substitute_term


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


def get_class_terms(graph: DiGraph) -> set[URIRef]:
    subclass_terms = {
        term
        for subj, obj, data in graph.edges(data=True)
        if data["label"] == RDFS.subClassOf
        for term in (subj, obj)
    }
    type_terms = {
        obj for subj, obj, data in graph.edges(data=True) if data["label"] == RDF.type
    }
    return subclass_terms | type_terms


def get_term_value(subj: URIRef, pred: URIRef, ref_rdf_graph: Graph):
    return ref_rdf_graph.value(subj, pred)


def bind_prefixes(rdf_graph: Graph, prefixes: dict[str, URIRef | Namespace]) -> Graph:
    for prefix, ns in prefixes.items():
        rdf_graph.bind(prefix, ns)
    return rdf_graph


def add_rdf_triples(
    rdf_graph: Graph,
    triples: Iterable[tuple[URIRef | Literal, URIRef, URIRef | Literal]],
) -> Graph:
    # TODO: set to strictly immutable rdf_graph
    return reduce(lambda graph, triple: graph.add(triple), triples, rdf_graph)


def add_labels(rdf_graph: Graph, term: URIRef, labels: list[str]) -> Graph:
    # assume the first element of the labels is the actual label, others are alt-names
    # TODO: set to strictly immutable rdf_graph
    if labels:
        rdf_graph = rdf_graph.add((term, RDFS.label, Literal(labels[0])))
        if len(labels) > 1:
            rdf_graph = add_rdf_triples(
                rdf_graph,
                ((term, SKOS.altLabel, Literal(label)) for label in labels[1:]),
            )
    return rdf_graph


def get_term_domain(term: URIRef, graph: DiGraph) -> Iterable[URIRef]:
    return (subj for subj, _, data in graph.edges(data=True) if data["label"] == term)


def get_term_range(term: URIRef, graph: DiGraph) -> Iterable[URIRef]:
    return (obj for _, obj, data in graph.edges(data=True) if data["label"] == term)


def get_domains_ranges(
    predicate: Iterable[URIRef], graph: DiGraph
) -> tuple[URIRef, Iterable[URIRef], Iterable[URIRef]]:
    return (
        predicate,
        get_term_domain(predicate, graph),
        get_term_range(predicate, graph),
    )


def get_term_collection_triples(
    rdf_graph: Graph,
    head_term: Iterable[URIRef],
    member_terms: Iterable[URIRef],
    member_rel: URIRef,
    term_collection_rel: URIRef,
) -> list[tuple[URIRef, URIRef, URIRef]]:
    triples = []
    collection_node = BNode()
    Collection(rdf_graph, collection_node, member_terms)
    # create class that points to the collection
    collection_class = BNode()
    triples.append((collection_class, RDF.type, OWL.Class))
    # connect them all together
    triples.append((collection_class, member_rel, collection_node))
    triples.append((head_term, term_collection_rel, collection_class))
    return triples


def add_domains_ranges(
    term_domains_ranges: [URIRef, Iterable[URIRef], Iterable[URIRef]],
    rdf_graph: DiGraph,
) -> Graph:
    predicate_term, domains, ranges = term_domains_ranges
    # TODO: assume union for now but fix later
    domain_collection_triples = get_term_collection_triples(
        rdf_graph, predicate_term, domains, OWL.unionOf, RDFS.domain
    )
    range_collection_triples = get_term_collection_triples(
        rdf_graph, predicate_term, ranges, OWL.unionOf, RDFS.range
    )
    return add_rdf_triples(
        rdf_graph, domain_collection_triples + range_collection_triples
    )


def get_instances(
    rdf_graph: Graph, default_terms: set[URIRef], term_types: dict[URIRef, URIRef]
) -> set[URIRef]:
    return {
        subj
        for subj, obj in rdf_graph.subject_objects(RDF.type)
        if obj not in default_terms and term_types[obj] == OWL.Class
    }


def get_classes(
    rdf_graph: Graph, default_terms: set[URIRef], term_types: dict[URIRef, URIRef]
) -> set[URIRef]:
    instance_superclasses = {
        subj
        for subj, obj in rdf_graph.subject_objects(RDF.type)
        if obj not in default_terms and term_types[subj] == OWL.Class
    }
    subclass_terms = {
        term
        for subj, obj in rdf_graph.subject_objects(RDFS.subClassOf)
        for term in (subj, obj)
    }
    return instance_superclasses | subclass_terms


def get_predicates(rdf_graph: Graph, default_terms: set[URIRef]) -> set[URIRef]:
    # TODO: add the dynamic predicate retrieval from term matching
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
            # TODO: add pred check here for annotations
            is_strat = pred in {RDF.type, RDFS.subClassOf}
            if is_strat:
                graph.add_edge(subj, obj, label=pred, is_strat=is_strat)
            else:
                graph.add_edge(obj, subj, label=pred, is_strat=is_strat)
    return graph


def rename_edges(graph: DiGraph, rename_mapping: dict[URIRef, str]) -> DiGraph:
    edge_rename_mapping = dict()
    graph = graph.copy()
    for subj, obj, data in graph.edges(data=True):
        pred = data["label"]
        new_edge_label = rename_mapping[pred]
        data.update({"label": new_edge_label})
        edge_rename_mapping[(subj, obj)] = data
    nx.set_edge_attributes(graph, edge_rename_mapping)
    return graph
