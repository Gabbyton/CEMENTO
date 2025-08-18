from collections import defaultdict
from functools import partial, reduce
from itertools import chain
from pathlib import Path
from uuid import uuid4

import networkx as nx
from networkx import DiGraph
from rdflib import OWL, RDF, RDFS, SKOS, Literal, URIRef
from rdflib.collection import Collection

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
    term_to_str,
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
    ref_strat_preds.add(RDFS.subPropertyOf)

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
                chain(  # TODO: unify rank predicate enumeration
                    chain(*rdf_graph.subject_objects(RDFS.subClassOf)),
                    chain(*rdf_graph.subject_objects(RDFS.subPropertyOf)),
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
            # TODO: put into config ini file
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
        nx.set_node_attributes(graph, True, "is_in_diagram")

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

        # process axioms and restrictions, starting with non-containers
        axiomatic_predicates = [RDFS.domain, RDFS.range]
        axiom_term_to_str = partial(
            term_to_str, inv_prefixes=inv_prefixes, aliases=aliases
        )
        axiom_triples = list(
            rdf_graph.triples_choices((None, axiomatic_predicates, None))
        )
        add_edges = list()
        axiom_graph = DiGraph()
        for subj, pred, obj in axiom_triples:
            if all(
                [
                    term not in default_terms or term in exempted_terms
                    for term in (subj, obj)
                ]
            ):
                add_edges.append(
                    (
                        axiom_term_to_str(subj),
                        axiom_term_to_str(obj),
                        {
                            "label": axiom_term_to_str(pred, label_only=True),
                        },
                    )
                )
        axiom_graph.add_edges_from(add_edges)
        # TODO: set is_axiom to True globally to global axiom graph, prior to merge
        nx.set_node_attributes(axiom_graph, True, "is_axiom")
        graph.add_nodes_from(axiom_graph.nodes(data=True))
        graph.add_edges_from(axiom_graph.edges(data=True))

        # process container terms
        # TODO: use global constant once moved
        valid_collection_types = [
            OWL.unionOf,
            OWL.intersectionOf,
            OWL.complementOf,
        ]
        from rdflib import BNode

        collection_heads = set(rdf_graph.subjects(RDF.first, None))
        collection_members_list = {
            head: list(Collection(rdf_graph, head)) for head in collection_heads
        }
        collections = defaultdict(list)
        for head, members in collection_members_list.items():
            for member in members:
                if isinstance(member, BNode):
                    _, _, member = next(
                        iter(
                            rdf_graph.triples_choices(
                                (member, valid_collection_types, None)
                            )
                        ),
                        (None, None, None),
                    )
                if member is not None:
                    collections[head].append(member)
        collection_types = dict()
        for head in collection_heads:
            type_triples = iter(
                rdf_graph.triples_choices((None, valid_collection_types, head))
            )
            _, collection_type, _ = next(type_triples, (None, None, None))
            collection_types[head] = collection_type
        # process multiple values
        multiobjects = defaultdict(list)
        for subj, pred, obj in rdf_graph:
            multiobjects[
                f"{axiom_term_to_str(subj)}::{axiom_term_to_str(pred)}"
            ].append(obj)
        multiobjects = {
            key: values for key, values in multiobjects.items() if len(values) > 1
        }
        old_ties = []
        old_nodes = []
        new_ties = []
        new_nodes = []
        for key, values in multiobjects.items():
            subj, pred = key.split("::")
            new_key = str(uuid4()).split("-")[-1]
            collection_heads.add(new_key)
            collections.update({new_key: values})
            for value in values:
                value_str = axiom_term_to_str(value)
                old_ties.append((subj, value_str))
                old_nodes.append(value_str)
            new_ties.append(
                (
                    subj,
                    new_key,
                    {
                        "label": pred,
                        "is_collection": True,
                    },
                )
            )
            collection_types[new_key] = "mds:TripleSyntaxSugar"
            new_nodes.append((new_key, {"is_collection": True, "is_axiom": True}))
            old_node_attrs = {
                node: {"is_collection": True, "is_axiom": True} for node in old_nodes
            }
            nx.set_node_attributes(graph, old_node_attrs)
        graph.remove_edges_from(old_ties)
        graph.remove_nodes_from(old_nodes)
        graph.add_nodes_from(new_nodes)
        graph.add_edges_from(new_ties)

        for head, items in collections.items():
            for item in items:
                graph.add_edge(
                    axiom_term_to_str(head),
                    axiom_term_to_str(item),
                    label="mds:hasCollectionMember",
                    is_collection=True,
                )

        for head, collection_type in collection_types.items():
            if collection_type is not None:
                graph.add_edge(
                    axiom_term_to_str(collection_type),
                    axiom_term_to_str(head),
                    label="mds:CollectionType",
                    is_axiom=True,
                    is_collection=True,
                )
        return graph
