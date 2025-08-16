from collections.abc import Iterable
from itertools import chain
from pathlib import Path

import networkx as nx
import pandas as pd
from more_itertools import unique_everseen
from networkx import DiGraph
from rdflib import RDF, RDFS, Namespace, URIRef
from rdflib.namespace import split_uri

from cemento.term_matching.transforms import (
    get_entire_prop_family,
    get_substitute_mapping,
)

# from cemento.term_matching.transforms import substitute_term
from cemento.utils.utils import get_graph_root_nodes, get_subgraphs


def get_properties_in_file(
    search_keys: dict[str, list[str]],
    terms: Iterable[str],
    graph: DiGraph,
    defaults_folder: str | Path,
    inv_prefixes: dict[URIRef | Namespace, str],
) -> set[str]:
    # partially parse the graph matching subclasses and types to determine if something is an object property
    partially_substituted_values = get_substitute_mapping(
        search_keys=search_keys,
        search_pool={"rdfs:subClassOf": RDFS.subClassOf, "rdf:type": RDF.type},
        terms=terms,
    )
    partial_hierarchy_edges = (
        (subj, obj)
        for subj, obj, data in graph.edges(data=True)
        if "label" in data and data["label"] in partially_substituted_values.keys()
    )
    prop_family = get_entire_prop_family(defaults_folder, inv_prefixes)

    partial_hierarchy_nodes = list(chain(*partial_hierarchy_edges))
    partial_graph = graph.subgraph(partial_hierarchy_nodes).copy()
    partial_graph_trees = get_subgraphs(partial_graph)

    prop_family_mapping = dict()
    for prop in prop_family:
        ns, abbrev_term = split_uri(prop)
        prop_family_mapping[f"{inv_prefixes[ns]}:{abbrev_term.strip()}"] = prop

    predicate_terms = set()
    for tree in partial_graph_trees:
        tree = tree.reverse()
        root_nodes = get_graph_root_nodes(tree)
        prop_substitutions = get_substitute_mapping(
            search_keys, prop_family_mapping, root_nodes
        )
        if any([root in prop_substitutions for root in root_nodes]):
            predicate_terms.update(tree.nodes)
    predicate_terms -= prop_family
    return predicate_terms


def get_diagram_terms_iter_with_pred(
    graph: DiGraph, property_terms: set[str]
) -> Iterable[str, bool]:
    graph_nodes = graph.nodes
    edge_labels = nx.get_edge_attributes(graph, "label").values()
    terms = unique_everseen(chain(graph_nodes, edge_labels))
    return ((term, term in property_terms) for term in terms)


def get_diagram_terms_iter(graph: DiGraph) -> Iterable[str]:
    diagram_terms_from_edges = (
        term
        for subj, obj, data in graph.edges(data=True)
        for term in (subj, data["label"], obj)
        if term
    )
    return unique_everseen(chain(diagram_terms_from_edges, graph.nodes))


def save_substitute_log(
    substitution_results: dict[str, tuple[URIRef, Iterable[str], Iterable[str]]],
    log_substitution_path: str | Path,
) -> None:
    log_entries = [
        (original_term, search_key, term, score, matched_term)
        for original_term, (
            matched_term,
            search_keys,
            matches,
        ) in substitution_results.items()
        for (search_key, (term, score)) in zip(search_keys, matches, strict=False)
    ]
    df = pd.DataFrame(
        log_entries,
        columns=[
            "original_term",
            "search_key",
            "search_result",
            "score",
            "matched_term",
        ],
    )
    df.to_csv(log_substitution_path)
