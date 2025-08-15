from functools import reduce
from itertools import chain
from pathlib import Path

import networkx as nx
from networkx import DiGraph
from rdflib import OWL, RDF, RDFS, SKOS, Literal, URIRef

from cemento.rdf.transforms import (
    add_triples_to_digraph,
    assign_literal_ids,
    assign_literal_status,
    assign_pred_status,
    assign_rank_status,
    assign_strat_status,
    get_graph_relabel_mapping,
    get_literal_format_mapping,
    get_literal_values_with_id,
    rename_edges,
)
from cemento.term_matching.io import read_rdf
from cemento.term_matching.transforms import (
    get_aliases,
    get_default_terms,
    get_entire_prop_family,
    get_prefixes,
    get_strat_predicates,
)
from cemento.utils.constants import RDFFormat
from cemento.utils.io import (
    get_default_defaults_folder,
    get_default_prefixes_file,
    get_default_references_folder,
)


def convert_rdf_to_graph(
    input_path: str | Path,
    file_format: str | RDFFormat = None,
    classes_only: bool = False,
    onto_ref_folder: str | Path = None,
    defaults_folder: str | Path = None,
    prefixes_path: str | Path = None,
    set_unique_literals=True,
) -> DiGraph:
    onto_ref_folder = (
        get_default_references_folder() if not onto_ref_folder else onto_ref_folder
    )
    defaults_folder = (
        get_default_defaults_folder() if not defaults_folder else defaults_folder
    )
    prefixes_path = get_default_prefixes_file() if not prefixes_path else prefixes_path
    print("retrieving reference data...")
    file_strat_preds = set()
    ref_strat_preds = set()
    prefixes, inv_prefixes = get_prefixes(
        prefixes_path, onto_ref_folder, input_file=input_path
    )
    default_terms = get_default_terms(defaults_folder)

    if not classes_only:
        ref_strat_preds = set(
            get_strat_predicates(onto_ref_folder, defaults_folder, inv_prefixes)
        )
    # TODO: find better solution for including these options
    ref_strat_preds.add(RDFS.subClassOf)
    ref_strat_preds.add(RDF.type)

    with read_rdf(input_path, file_format=file_format) as rdf_graph:
        prefixes.update({key: value for key, value in rdf_graph.namespaces()})
        inv_prefixes.update({str(value): key for key, value in rdf_graph.namespaces()})
        print("retrieving terms...")

        file_uri_refs = set(
            filter(
                lambda x: isinstance(x, URIRef),
                rdf_graph.all_nodes(),
            )
        )
        all_classes = set(
            filter(
                lambda x: x in file_uri_refs,
                chain(
                    chain(*rdf_graph.subject_objects(RDFS.subClassOf)),
                    rdf_graph.objects(None, RDF.type),
                ),
            )
        )
        all_classes -= default_terms
        all_instances = set(
            filter(
                lambda x: x in file_uri_refs and x not in all_classes,
                rdf_graph.subjects(RDF.type),
            )
        )

        if not classes_only:
            # TODO: find a better solution for this section, move to transforms
            file_self_referentials = {
                pred for subj, pred, obj in rdf_graph if subj == obj
            }
            file_strat_pred_types = {
                OWL.AnnotationProperty,
                OWL.DatatypeProperty,
            }
            file_strat_preds = reduce(
                lambda acc, file_strat_pred: acc
                | set(rdf_graph.transitive_subjects(RDF.type, file_strat_pred)),
                file_strat_pred_types,
                set(),
            )
            syntax_reserved_preds = {RDFS.label, SKOS.altLabel}
            all_predicates = (
                (file_strat_preds | ref_strat_preds)
                - file_self_referentials
                - syntax_reserved_preds
            )

            all_literals = set(
                filter(lambda x: isinstance(x, Literal), rdf_graph.all_nodes())
            )
        else:
            all_predicates = {RDFS.subClassOf, RDF.type}
            all_literals = set()

        object_properties = set(
            rdf_graph.transitive_subjects(RDF.type, OWL.ObjectProperty)
        )
        all_predicates.update(object_properties)

        if set_unique_literals:
            print("creating unique literals...")
            literal_replacements = get_literal_values_with_id(all_literals)
            rdf_graph = assign_literal_ids(rdf_graph, literal_replacements)
            all_literals = set(
                filter(lambda x: isinstance(x, Literal), rdf_graph.all_nodes())
            )

        display_set = all_classes

        exempted_terms = set()
        if not classes_only:
            display_set = all_classes | all_instances | all_literals
            exempted_terms = get_entire_prop_family(defaults_folder, inv_prefixes)

        # TODO: find a better solution for exemptions, possible include all transitive objects for rdf:subClassOf
        display_set.update(exempted_terms)

        exclude_terms = default_terms - exempted_terms
        display_terms = set(
            filter(
                lambda term: term not in exclude_terms,
                display_set,
            )
        )
        graph_triples = [
            (subj, pred, obj)
            for subj, pred, obj in rdf_graph
            if (subj in display_terms and obj in display_terms)
            and pred in all_predicates
        ]
        graph = DiGraph()
        graph = reduce(
            lambda graph, triple: add_triples_to_digraph(*triple, graph),
            graph_triples,
            graph,
        )

        print("assigining additional properties...")
        graph = assign_strat_status(
            graph, strat_terms=(ref_strat_preds | file_strat_preds)
        )
        # TODO: assign literal status from read drawio as well
        graph = assign_literal_status(graph, all_literals)
        graph = assign_rank_status(graph)
        graph = assign_pred_status(graph)
        nx.set_node_attributes(
            graph,
            {
                node: {"is_class": node in all_classes or node in exempted_terms}
                for node in graph.nodes()
            },
        )
        nx.set_node_attributes(
            graph,
            {node: {"is_instance": node in all_instances} for node in graph.nodes()},
        )

        print("renaming terms...")
        all_terms = all_classes | all_instances | all_predicates
        aliases = get_aliases(rdf_graph)
        rename_terms = get_graph_relabel_mapping(
            all_terms, all_classes, all_instances, aliases, inv_prefixes
        )
        graph = nx.relabel_nodes(graph, rename_terms)
        graph = rename_edges(graph, rename_terms)

        print("formatting literals...")
        rename_format_literals = get_literal_format_mapping(graph, inv_prefixes)
        graph = nx.relabel_nodes(graph, rename_format_literals)
        return graph
