from functools import reduce
from pathlib import Path

import networkx as nx
from networkx import DiGraph
from rdflib import RDF, RDFS, SKOS, URIRef

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
from cemento.term_matching.constants import get_default_namespace_prefixes
from cemento.term_matching.io import read_ttl
from cemento.term_matching.transforms import (
    get_aliases,
    get_prefixes,
    get_strat_predicates,
    get_term_types,
)


def convert_ttl_to_graph(
    input_path: str | Path,
    onto_ref_folder: str | Path = None,
    defaults_folder: str | Path = None,
    prefixes_path: str | Path = None,
    check_ttl_validity: bool = True,
    set_unique_literals=True,
) -> DiGraph:

    file_args = [onto_ref_folder, prefixes_path, defaults_folder]
    if not all(file_args) and any(file_args):
        raise ValueError("Either all the folders are set or none at all!")

    prefixes, inv_prefixes = get_prefixes(prefixes_path, onto_ref_folder)
    default_namespace_prefixes = get_default_namespace_prefixes()
    default_terms = {
        term
        for ns in default_namespace_prefixes.values()
        for term in dir(ns)
        if isinstance(term, URIRef)
    }
    strat_props = set(
        get_strat_predicates(onto_ref_folder, defaults_folder, inv_prefixes)
    )
    # TODO: find better solution for including these options
    strat_props.add(RDFS.subClassOf)
    strat_props.add(RDF.type)

    with read_ttl(input_path) as rdf_graph:

        if check_ttl_validity:
            check_graph_validity(rdf_graph)

        term_types = get_term_types(rdf_graph)
        all_classes = get_classes(rdf_graph, default_terms, term_types)
        all_instances = get_instances(rdf_graph, default_terms, term_types)
        all_predicates = get_predicates(rdf_graph, default_terms)
        all_predicates.update([RDF.type, RDFS.subClassOf])
        all_predicates.add(SKOS.definition)
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

        graph = assign_strat_status(graph, strat_terms=strat_props)
        # print(graph.edges(data=True))
        # TODO: assign literal status from read drawio as well
        graph = assign_literal_status(graph, all_literals)

        all_terms = all_classes | all_instances | all_predicates | default_terms
        aliases = get_aliases(rdf_graph)
        rename_terms = get_graph_relabel_mapping(
            all_terms, all_classes, all_instances, aliases, inv_prefixes
        )
        graph = nx.relabel_nodes(graph, rename_terms)
        graph = rename_edges(graph, rename_terms)
        rename_format_literals = get_literal_format_mapping(graph)
        graph = nx.relabel_nodes(graph, rename_format_literals)
        return graph
