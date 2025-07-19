from functools import reduce
from pathlib import Path

import networkx as nx
from networkx import DiGraph
from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS, URIRef

from cemento.rdf.transforms import (
    add_triples_to_digraph,
    assign_literal_ids,
    assign_literal_status,
    assign_strat_status,
    check_graph_validity,
    get_classes,
    get_graph_relabel_mapping,
    get_instances,
    get_literal_format_mapping,
    get_literal_values_with_id,
    get_literals,
    get_predicates,
    rename_edges,
)
from cemento.term_matching.io import read_ttl
from cemento.term_matching.transforms import get_aliases, get_term_types


def convert_ttl_to_graph(
    input_path: str | Path, check_ttl_validity: bool = True, set_unique_literals=True
) -> DiGraph:
    default_namespaces = [RDF, RDFS, OWL, DCTERMS, SKOS]
    default_namespace_prefixes = ["rdf", "rdfs", "owl", "dcterms", "skos"]

    with read_ttl(input_path) as rdf_graph:

        if check_ttl_validity:
            check_graph_validity(rdf_graph)

        prefixes = {prefix: ns for prefix, ns in rdf_graph.namespaces()}
        prefixes.update(
            {
                prefix: ns
                for prefix, ns in zip(
                    default_namespace_prefixes, default_namespaces, strict=True
                )
            }
        )

        inv_prefix = {str(value): key for key, value in prefixes.items()}

        default_terms = {
            term
            for ns in default_namespaces
            for term in dir(ns)
            if isinstance(term, URIRef)
        }

        term_types = get_term_types(rdf_graph)
        all_classes = get_classes(rdf_graph, default_terms, term_types)
        all_instances = get_instances(rdf_graph, default_terms, term_types)
        all_predicates = get_predicates(rdf_graph, default_terms)
        all_predicates.update([RDF.type, RDFS.subClassOf])
        all_literals = get_literals(rdf_graph)

        if set_unique_literals:
            literal_replacements = get_literal_values_with_id(all_literals)
            rdf_graph = assign_literal_ids(rdf_graph, literal_replacements)

        graph = DiGraph()
        graph_triples = (
            (subj, pred, obj)
            for subj, pred, obj in rdf_graph
            if subj not in default_terms
            and obj not in default_terms
            and pred in all_predicates
        )
        graph = reduce(
            lambda graph, triples: add_triples_to_digraph(*triples, graph),
            graph_triples,
            graph,
        )

        graph = assign_strat_status(graph)
        # TODO: assign literal status from read drawio as well
        graph = assign_literal_status(graph, all_literals)

        all_terms = all_classes | all_instances | all_predicates | default_terms
        aliases = get_aliases(rdf_graph)
        rename_terms = get_graph_relabel_mapping(
            all_terms, all_classes, all_instances, aliases, inv_prefix
        )
        graph = nx.relabel_nodes(graph, rename_terms)
        graph = rename_edges(graph, rename_terms)
        rename_format_literals = get_literal_format_mapping(graph)
        graph = nx.relabel_nodes(graph, rename_format_literals)
        return graph
