import json
import os
import re
from collections import defaultdict
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from functools import partial
from pathlib import Path

import networkx as nx
import rdflib
from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS, Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import split_uri
from thefuzz import fuzz, process

from cemento.draw_io.read_diagram import ReadDiagram

INPUT_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/SyncXrayResult_graph.drawio"
ONTO_FOLDER = "/Users/gabriel/dev/sdle/CEMENTO/data"
PREFIXES_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/prefixes.json"
TTL_OUTPUT_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/output.ttl"
DRAWIO_OUTPUT_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/output.drawio"


@contextmanager
def read_ttl(file_path: str | Path) -> Graph:
    rdf_graph = Graph()
    try:
        rdf_graph.parse(file_path, format="turtle")
        yield rdf_graph
    finally:
        rdf_graph.close()


def merge_dictionaries(dict_list: list[dict[any, any]]) -> dict[any, any]:
    return {key: value for each_dict in dict_list for key, value in each_dict.items()}


def read_prefixes_from_json(file_path: str) -> dict[str, URIRef]:
    with open(file_path, "r") as f:
        prefixes = json.load(f)
        return prefixes


def get_search_terms_from_defaults(
    default_namespace_prefixes: dict[str, Namespace],
) -> dict[str, URIRef]:
    search_terms = dict()
    for prefix, ns in default_namespace_prefixes.items():
        for term in dir(ns):
            if isinstance(term, rdflib.URIRef):
                _, name = split_uri(term)
                search_terms[f"{prefix}:{name}"] = term
    return search_terms


def iterate_ttl_graphs(
    folder_path: str, graph_function: Callable[[Graph], any]
) -> list[any]:
    results = []
    for file in os.scandir(folder_path):
        file_path = Path(file.path)
        if file_path.suffix == ".ttl":
            with read_ttl(file_path) as graph:
                result = graph_function(graph)
                results.append(result)
    return results


def read_prefixes_from_graph(rdf_graph: Graph) -> dict[str, str]:
    return {prefix: str(ns) for prefix, ns in rdf_graph.namespaces()}


def get_search_terms_from_graph(
    rdf_graph: Graph, inv_prefixes: dict[str, str]
) -> dict[str, URIRef]:
    search_terms = dict()
    all_terms = set()
    for subj, pred, obj in rdf_graph:
        all_terms.update([subj, pred, obj])

        if pred == RDFS.label and pred == SKOS.altLabel:
            ns, _ = split_uri(subj)
            prefix = inv_prefixes[ns]
            search_terms[f"{prefix}:{str(obj)}"] = subj

    for term in all_terms:
        if isinstance(term, rdflib.URIRef):
            ns, abbrev_term = split_uri(term)
            prefix = inv_prefixes[str(ns)]
            search_terms[f"{prefix}:{abbrev_term}"] = term

    return search_terms


def get_abbrev_term(term: str, is_predicate=False) -> tuple[str, str]:
    prefix = None
    abbrev_term = term
    strict_camel_case = False

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
    default_prefix: str = "mds",
):
    if prefix is None:
        prefix = default_prefix
    ns_uri = prefixes[prefix]
    return rdflib.URIRef(f"{ns_uri}{abbrev_term}")


def substitute_term(
    term: URIRef, search_keys: Iterable[str], search_terms: dict[str, URIRef]
):
    best_match, score = max(
        (
            result
            for search_key in search_keys
            if (
                result := process.extractOne(
                    search_key,
                    search_terms,
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=75,
                )
            )
            is not None
        ),
        key=lambda x: x[1] if x is not None else -1,
        default=(term, -1),
    )
    return search_terms[best_match] if best_match != term else term


if __name__ == "__main__":
    default_namespaces = [RDF, RDFS, OWL, DCTERMS, SKOS]
    default_namespace_prefixes = ["rdf", "rdfs", "owl", "dcterms", "skos"]

    prefixes = read_prefixes_from_json(PREFIXES_PATH)

    default_namespace_prefixes = {
        prefix: ns for prefix, ns in zip(default_namespace_prefixes, default_namespaces)
    }
    prefixes.update(default_namespace_prefixes)

    search_terms = get_search_terms_from_defaults(default_namespace_prefixes)
    file_prefixes = iterate_ttl_graphs(ONTO_FOLDER, read_prefixes_from_graph)
    prefixes |= merge_dictionaries(file_prefixes)
    inv_prefixes = {value: key for key, value in prefixes.items()}
    file_search_terms = iterate_ttl_graphs(
        ONTO_FOLDER, partial(get_search_terms_from_graph, inv_prefixes=inv_prefixes)
    )
    search_terms |= merge_dictionaries(file_prefixes)

    # read the diagram and retrieve the relationship triples as a dataframe
    diagram = ReadDiagram(INPUT_PATH)
    rels = diagram.get_relationships()

    terms = {
        (term, term == row["rel"])
        for _, row in rels.iterrows()
        for term in (row["parent"], row["child"], row["rel"])
    }

    constructed_terms = {
        term: construct_term_uri(
            *get_abbrev_term(term, is_predicate=is_predicate), prefixes=prefixes
        )
        for term, is_predicate in terms
    }

    for term, _ in terms:
        _, abbrev_term = get_abbrev_term(term)
        undo_camel_case_term = " ".join(
            re.findall(r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z][a-z]+|[0-9]+", abbrev_term)
        )
        search_keys = [term, abbrev_term, undo_camel_case_term]
        constructed_terms[term] = substitute_term(constructed_terms[term], search_keys, search_terms)

    graph = nx.DiGraph()
    for _, row in rels.iterrows():
        subj, obj, pred = row["parent"], row["child"], row["rel"]
        subj, obj, pred = tuple(constructed_terms[key] for key in (subj, pred, obj))
        graph.add_edge(subj, obj, label=pred)

    # # iterate through the edges to get all classes
    # for subj, term, data in g.edges(data=True):
    #     predicate = data["label"]

    #     if predicate == RDFS.subClassOf:
    #         # we assume terms between RDFS.subClassOf is a class
    #         class_terms.update([subj, term])

    #     if predicate == RDF.type:
    #         # we assume the object of an RDF.type is also a class
    #         class_terms.add(term)

    # # create the rdf graph to store the ttl output
    # rdf_graph = rdflib.Graph()

    # # bind prefixes to namespaces for the rdf graph
    # for prefix in prefixes:
    #     rdf_graph.bind(prefix, prefixes[prefix])

    # # collect edge inputs and outputs on object properties and consider them the domains and ranges
    # # TODO: assume union of terms for now, fix later
    # predicate_domain = defaultdict(list)
    # predicate_range = defaultdict(list)
    # for domain_term, range_term, data in g.edges(data=True):
    #     predicate_term = data["label"]
    #     predicate_domain[predicate_term].append(domain_term)
    #     predicate_range[predicate_term].append(range_term)

    # # combine node and edge objects into one collection of terms
    # all_edges = {data["label"] for _, _, data in g.edges(data=True)}
    # all_terms = g.nodes() | all_edges

    # # iterate through all the terms and predicates
    # for term in all_terms:
    #     # for each term, retrieve the prefix and the search term for retrieving the saved object
    #     ns, abbrev_term = split_uri(term)
    #     prefix = inv_prefixes[str(ns)]
    #     search_term = f"{prefix}:{abbrev_term}"

    #     # if the class is a term, always add the type to the ttl file
    #     if term in class_terms:
    #         rdf_graph.add((term, RDF.type, OWL.Class))

    #     # check if the prefix is not default
    #     if prefix not in default_namespace_prefixes:
    #         # if the term is a predicate and is not part of the default namespaces, add an object property type to the ttl file
    #         if term in predicate_terms:
    #             # TODO: Assume all predicates are object properties for now, change later
    #             rdf_graph.add((term, RDF.type, OWL.ObjectProperty))

    #         # if the term is already imported from somewhere else
    #         if search_term in search_terms:
    #             exact_term = search_terms[search_term]
    #             term_type = search_term_onto_graph.value(exact_term, RDF.type)
    #             label = search_term_onto_graph.value(exact_term, RDFS.label)

    #             # get the type and label if available and add to the ttl file
    #             if term_type:
    #                 rdf_graph.add((term, RDF.type, term_type))

    #             if label:
    #                 rdf_graph.add((term, RDFS.label, label))

    #             # add an exact match to the ttl file for easier cross-referencing
    #             rdf_graph.add((term, SKOS.exactMatch, exact_term))
    #         elif term in predicate_terms:
    #             # if the term is not default and is new, add domains and ranges for the object property to the ttl file entry
    #             # iterate over the RDFS.domain, RDFS.range and predicate domain and range respectively.
    #             for dom_or_range_term, term_dom_range in {
    #                 RDFS.domain: predicate_domain[term],
    #                 RDFS.range: predicate_range[term],
    #             }.items():
    #                 if term_dom_range:
    #                     # if there are more than one term, save the domain or range as a collection
    #                     if len(term_dom_range) > 1:
    #                         collection_node = rdflib.BNode()
    #                         collection_list = Collection(
    #                             rdf_graph, collection_node, term_dom_range
    #                         )
    #                         # create class that points to the collection
    #                         collection_class = rdflib.BNode()
    #                         rdf_graph.add((collection_class, RDF.type, OWL.Class))
    #                         # connect them all together
    #                         # TODO: assume union for now but fix later
    #                         rdf_graph.add(
    #                             (collection_class, OWL.unionOf, collection_node)
    #                         )
    #                         rdf_graph.add((term, dom_or_range_term, collection_class))
    #                     else:
    #                         # if there is only one term, use that term directly
    #                         rdf_graph.add((term, dom_or_range_term, term_dom_range[0]))

    # # now add the triples from the drawio diagram
    # for domain_term, range_term, data in g.edges(data=True):
    #     predicate_term = data["label"]
    #     rdf_graph.add((domain_term, predicate_term, range_term))
    # # serialize the output as a turtle file
    # rdf_graph.serialize(TTL_OUTPUT_PATH)
    # print(
    #     "\n".join(
    #         [f"{term} -> {key} ({score})" for term, key, score in substituted_terms]
    #     )
    # )
