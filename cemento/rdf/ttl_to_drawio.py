import networkx as nx
from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS, URIRef

from cemento.draw_io.write_diagram import WriteDiagram
from cemento.rdf.io import read_ttl
from cemento.rdf.transforms import (
    get_aliases,
    get_graph,
    get_graph_relabel_mapping,
    get_term_types,
    get_terms,
    rename_edges,
)
from cemento.tree import Tree


def convert_ttl_to_drawio(input_path, output_path):
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

        term_type = get_term_types(rdf_graph)
        all_classes, all_instances, all_predicates = get_terms(
            rdf_graph, term_type, default_terms
        )

        graph = get_graph(rdf_graph, all_predicates, default_terms)

        all_terms = all_classes | all_instances | all_predicates | default_terms
        aliases = get_aliases(rdf_graph)
        rename_terms = get_graph_relabel_mapping(
            all_terms, aliases, inv_prefix, all_classes, all_instances
        )
        graph = nx.relabel_nodes(graph, rename_terms)
        graph = rename_edges(graph, rename_terms)

    tree = Tree(graph=graph, do_gen_ids=True, invert_tree=False)
    diagram = WriteDiagram(output_path)
    tree.draw_tree(write_diagram=diagram)
    diagram.draw()
