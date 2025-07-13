import json
import os
import re
from collections import defaultdict
from pathlib import Path

import networkx as nx
import rdflib
from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS
from rdflib.collection import Collection
from rdflib.namespace import split_uri
from thefuzz import fuzz, process

from cemento.draw_io.read_diagram import ReadDiagram

INPUT_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/SyncXrayResult_graph.drawio"
ONTO_FOLDER = "/Users/gabriel/dev/sdle/CEMENTO/data"
PREFIXES_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/prefixes.json"
TTL_OUTPUT_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/output.ttl"
DRAWIO_OUTPUT_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/output.drawio"

if __name__ == "__main__":
    prefixes = dict()
    inv_prefixes = dict()
    with open(PREFIXES_PATH, "r") as f:
        prefixes = json.load(f)

    # load up namespaces for matching terms
    search_terms = dict()

    # load up default namespaces from rdflib
    default_namespaces = [RDF, RDFS, OWL, DCTERMS, SKOS]
    default_namespace_prefixes = ["rdf", "rdfs", "owl", "dcterms", "skos"]
    default_namespaces = {
        key: value for key, value in zip(default_namespace_prefixes, default_namespaces)
    }
    # add default namespaces to global prefixes dict
    prefixes.update(default_namespaces)

    # for each of the terms under the default namespaces ,retrieve the terms to a list of search terms
    for prefix, ns in default_namespaces.items():
        for term in dir(ns):
            if isinstance(term, rdflib.URIRef):
                _, name = split_uri(term)
                # prefix the terms with the the default prefix
                search_terms[f"{prefix}:{name}"] = term

    # load up all files in the data folder and save them to terms
    onto_files = [
        Path(file.path)
        for file in os.scandir(ONTO_FOLDER)
        if Path(file.path).suffix == ".ttl"
    ]

    # initialize an rdf graph aggregating all input files
    search_term_onto_graph = rdflib.Graph()
    # for each file in the data folder, add triples to the graph
    for onto_file in onto_files:
        local_onto_graph = rdflib.Graph()
        search_term_onto_graph.parse(onto_file, format="turtle")
        # create an rdf graph local to the current file
        local_onto_graph.parse(onto_file, format="turtle")

        # update the dictionary with this file's prefixes
        prefixes.update({prefix: ns for prefix, ns in local_onto_graph.namespaces()})

        # reverse the values to get prefix from namespace
        inv_prefixes = {str(value): key for key, value in prefixes.items()}

        all_terms = set()
        # TODO: using file name as the local prefix, find better way to handle
        # assign a local prefix to the file, for when users mistake terms to belong to the file prefix
        local_prefix = onto_file.stem
        for subj, pred, term in local_onto_graph:
            # collect all terms in the file
            all_terms.update([subj, pred, term])
            # save all term aliases in a global dictionary
            if (
                pred == RDFS.label
                or pred == SKOS.altLabel
                and isinstance(subj, rdflib.URIRef)
            ):
                # get the prefix from the namespace of the term
                ns, _ = split_uri(subj)
                prefix = inv_prefixes[str(ns)]
                # save the alias as a search term with its actual prefix, and map to the term
                search_terms[f"{prefix}:{str(term)}"] = subj
        # for all collected terms in the file, also save the abbreviated uri as a search term with the actual prefix
        for term in all_terms:
            if isinstance(term, rdflib.URIRef):
                ns, abbrev_term = split_uri(term)
                prefix = inv_prefixes[str(ns)]
                search_terms[f"{prefix}:{abbrev_term}"] = term

    # read the diagram and retrieve the relationship triples as a dataframe
    diagram = ReadDiagram(INPUT_PATH)
    rels = diagram.get_relationships()

    # initialize a directed graph to save the parsed triples
    g = nx.DiGraph()

    terms = dict()
    class_terms = set()
    predicate_terms = set()

    substituted_terms = []

    # iterate through the relationship triples (df rows)
    for _, row in rels.iterrows():
        subj, obj, rel = (row["parent"], row["child"], row["rel"])

        term_items = [subj, obj, rel]
        # parse each of the terms in the triple
        for idx, term in enumerate(term_items):
            # split the term between the prefix and the abbreviated uri
            if ":" in term:
                prefix, abbrev_term = term.split(":")
                raw_abbrev_term = abbrev_term
            else:
                prefix = None
                abbrev_term = term

            # if there is no prefix, automatically set as an mds term
            if prefix is None:
                # set the namspace uri to the value mapped to the prefix
                ns_uri = prefixes["mds"]
            elif prefix not in prefixes:
                # if there are no prefixes matching, the master file is incomplete or the ttl was not constructed correctly
                raise KeyError(
                    f"Cannot find prefix {prefix} in prefix master list. Consider adding it."
                )
            else:
                ns_uri = prefixes[prefix]

            # if the term is a predicate, replace underscores with spaces and enforce lowercase start
            strict_camel_case = False
            if idx == len(term_items) - 1:
                abbrev_term = abbrev_term.replace("_", " ")
                strict_camel_case = True

            # if the term is a class, use upper camel case / Pascal case
            abbrev_term = "".join(
                [
                    f"{word[0].upper()}{word[1:] if len(word) > 1 else ''}"
                    for word in abbrev_term.split()
                ]
            )

            if strict_camel_case and term[0].islower():
                abbrev_term = f"{abbrev_term[0].lower()}{abbrev_term[1:] if len(abbrev_term) > 1 else ''}"

            # set the term uri as a valid rdflib URIRef object
            term_uri = rdflib.URIRef(f"{ns_uri}{abbrev_term}")

            # TODO: potentially add a key for a new term, i.e. *
            # if the term already exists in the input ontologies, defer to use those terms
            if prefix in prefixes and "*" not in term:
                # search for the closest term to the input from the list of collected search terms
                subs = []
                undo_camel_case_term = " ".join(
                    re.findall(
                        r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z][a-z]+|[0-9]+", abbrev_term
                    )
                )
                for search_key in [raw_abbrev_term, abbrev_term, undo_camel_case_term]:
                    term_search_key = f"{prefix}:{search_key.strip()}"
                    sub = process.extractOne(
                        term_search_key,
                        search_terms.keys(),
                        scorer=fuzz.token_sort_ratio,
                        score_cutoff=75,  # arbitrarily set but functional
                        # TODO: determine an ideal cutoff for terms
                        # TODO: output substituted terms to the user to verify if within the warning
                    )
                    if sub:
                        subs.append(sub)
                if subs:
                    sorted(subs, key=lambda x: x[1], reverse=True)
                    sub = next(iter(subs))
                    # if a substitution is made, use that terms URIRef object instead
                    term_key, score = sub
                    term_uri = search_terms[term_key]
                    # print(f"{term} -> {term_key} ({score})")
                    # save substituted terms for user debugging
                    # TODO: implement user send of substituted terms
                    substituted_terms.append((term, term_key, score))

            # save the terms to map the drawio input to the actual URIRef object for that term
            terms[term] = term_uri

        # add predicate terms to a set for identification
        predicate_terms.add(terms[rel])

        # add the triple as an edge to the graph with the proper rdflib objects
        g.add_edge(terms[subj], terms[obj], label=terms[rel])

    # iterate through the edges to get all classes
    for subj, term, data in g.edges(data=True):
        predicate = data["label"]

        if predicate == RDFS.subClassOf:
            # we assume terms between RDFS.subClassOf is a class
            class_terms.update([subj, term])

        if predicate == RDF.type:
            # we assume the object of an RDF.type is also a class
            class_terms.add(term)

    # create the rdf graph to store the ttl output
    rdf_graph = rdflib.Graph()

    # bind prefixes to namespaces for the rdf graph
    for prefix in prefixes:
        rdf_graph.bind(prefix, prefixes[prefix])

    # collect edge inputs and outputs on object properties and consider them the domains and ranges
    # TODO: assume union of terms for now, fix later
    predicate_domain = defaultdict(list)
    predicate_range = defaultdict(list)
    for domain_term, range_term, data in g.edges(data=True):
        predicate_term = data["label"]
        predicate_domain[predicate_term].append(domain_term)
        predicate_range[predicate_term].append(range_term)

    # combine node and edge objects into one collection of terms
    all_edges = {data["label"] for _, _, data in g.edges(data=True)}
    all_terms = g.nodes() | all_edges

    # iterate through all the terms and predicates
    for term in all_terms:
        # for each term, retrieve the prefix and the search term for retrieving the saved object
        ns, abbrev_term = split_uri(term)
        prefix = inv_prefixes[str(ns)]
        search_term = f"{prefix}:{abbrev_term}"

        # if the class is a term, always add the type to the ttl file
        if term in class_terms:
            rdf_graph.add((term, RDF.type, OWL.Class))

        # check if the prefix is not default
        if prefix not in default_namespace_prefixes:
            # if the term is a predicate and is not part of the default namespaces, add an object property type to the ttl file
            if term in predicate_terms:
                # TODO: Assume all predicates are object properties for now, change later
                rdf_graph.add((term, RDF.type, OWL.ObjectProperty))

            # if the term is already imported from somewhere else
            if search_term in search_terms:
                exact_term = search_terms[search_term]
                term_type = search_term_onto_graph.value(exact_term, RDF.type)
                label = search_term_onto_graph.value(exact_term, RDFS.label)

                # get the type and label if available and add to the ttl file
                if term_type:
                    rdf_graph.add((term, RDF.type, term_type))

                if label:
                    rdf_graph.add((term, RDFS.label, label))

                # add an exact match to the ttl file for easier cross-referencing
                rdf_graph.add((term, SKOS.exactMatch, exact_term))
            elif term in predicate_terms:
                # if the term is not default and is new, add domains and ranges for the object property to the ttl file entry
                # iterate over the RDFS.domain, RDFS.range and predicate domain and range respectively.
                for dom_or_range_term, term_dom_range in {
                    RDFS.domain: predicate_domain[term],
                    RDFS.range: predicate_range[term],
                }.items():
                    if term_dom_range:
                        # if there are more than one term, save the domain or range as a collection
                        if len(term_dom_range) > 1:
                            collection_node = rdflib.BNode()
                            collection_list = Collection(
                                rdf_graph, collection_node, term_dom_range
                            )
                            # create class that points to the collection
                            collection_class = rdflib.BNode()
                            rdf_graph.add((collection_class, RDF.type, OWL.Class))
                            # connect them all together
                            # TODO: assume union for now but fix later
                            rdf_graph.add(
                                (collection_class, OWL.unionOf, collection_node)
                            )
                            rdf_graph.add((term, dom_or_range_term, collection_class))
                        else:
                            # if there is only one term, use that term directly
                            rdf_graph.add((term, dom_or_range_term, term_dom_range[0]))

    # now add the triples from the drawio diagram
    for domain_term, range_term, data in g.edges(data=True):
        predicate_term = data["label"]
        rdf_graph.add((domain_term, predicate_term, range_term))
    # serialize the output as a turtle file
    rdf_graph.serialize(TTL_OUTPUT_PATH)
    print(
        "\n".join(
            [f"{term} -> {key} ({score})" for term, key, score in substituted_terms]
        )
    )
