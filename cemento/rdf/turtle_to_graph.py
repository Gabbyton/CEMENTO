from pathlib import Path

import networkx as nx
from networkx import DiGraph
from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS, URIRef

from cemento.rdf.io import read_ttl
from cemento.rdf.transforms import (
    get_aliases,
    get_classes,
    get_graph,
    get_graph_relabel_mapping,
    get_instances,
    get_predicates,
    get_term_types,
    rename_edges,
)


def convert_ttl_to_graph(input_path: str | Path) -> DiGraph:
    default_namespaces = [RDF, RDFS, OWL, DCTERMS, SKOS]
    default_namespace_prefixes = ["rdf", "rdfs", "owl", "dcterms", "skos"]

    with read_ttl(input_path) as rdf_graph:

        prefixes = {prefix: ns for prefix, ns in rdf_graph.namespaces()}
        prefixes.update(
            {
                prefix: ns
                for prefix, ns in zip(default_namespace_prefixes, default_namespaces)
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
        graph = get_graph(rdf_graph, all_predicates, default_terms)

        all_terms = all_classes | all_instances | all_predicates | default_terms
        aliases = get_aliases(rdf_graph)
        rename_terms = get_graph_relabel_mapping(
            all_terms, all_classes, all_instances, aliases, inv_prefix
        )

        graph = nx.relabel_nodes(graph, rename_terms)
        graph = rename_edges(graph, rename_terms)
        return graph
