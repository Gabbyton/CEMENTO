import json
import os
from collections import defaultdict
from pathlib import Path

import networkx as nx
import rdflib
from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS
from rdflib.collection import Collection
from rdflib.namespace import split_uri
from thefuzz import fuzz, process

from cemento.draw_io.read_diagram import ReadDiagram

from cemento.rdf.read_turtle import ReadTurtle
from cemento.tree import Tree
from cemento.draw_io.write_diagram import WriteDiagram

INPUT_PATH = "/srv/samba-share/mds/mds-onto/CEMENTO/SyncXrayResult_graph.drawio"
ONTO_FOLDER = "/srv/samba-share/mds/mds-onto/CEMENTO/data"

if __name__ == "__main__":
    prefixes = dict()
    with open("prefixes.json", "r") as f:
        prefixes = json.load(f)

    # load up namespaces for matching terms
    search_terms = dict()

    # load up default namespaces from rdflib
    default_namespaces = [RDF, RDFS, OWL, DCTERMS, SKOS]
    default_namespace_prefixes = ["rdf", "rdfs", "owl", "dcterms", "skos"]
    default_namespaces = {
        key: value for key, value in zip(default_namespace_prefixes, default_namespaces)
    }
    prefixes.update(default_namespaces)

    for prefix, ns in default_namespaces.items():
        for term in dir(ns):
            if isinstance(term, rdflib.URIRef):
                _, name = split_uri(term)
                search_terms[f"{prefix}:{name}"] = term

    # load up all files in the data folder and save them to terms
    onto_files = [
        Path(file.path)
        for file in os.scandir(ONTO_FOLDER)
        if Path(file.path).suffix == ".ttl"
    ]

    search_term_onto_graph = rdflib.Graph()
    for onto_file in onto_files:
        local_onto_graph = rdflib.Graph()
        search_term_onto_graph.parse(onto_file, format="turtle")
        local_onto_graph.parse(onto_file, format="turtle")

        prefixes.update({prefix: ns for prefix, ns in local_onto_graph.namespaces()})

        inv_prefixes = {str(value): key for key, value in prefixes.items()}

        all_terms = set()
        # TODO: using file name as the local prefix, find better way to handle
        local_prefix = onto_file.stem
        for subj, pred, obj in local_onto_graph:
            all_terms.update([subj, pred, obj])
            if (
                pred == RDFS.label
                or pred == SKOS.altLabel
                and isinstance(subj, rdflib.URIRef)
            ):
                ns, _ = split_uri(subj)
                prefix = inv_prefixes[str(ns)]
                search_terms[f"{prefix}:{str(obj)}"] = subj
                search_terms[f"{local_prefix}:{str(obj)}"] = subj
        for term in all_terms:
            if isinstance(term, rdflib.URIRef):
                ns, abbrev_term = split_uri(term)
                prefix = inv_prefixes[str(ns)]
                search_terms[f"{prefix}:{abbrev_term}"] = term
                search_terms[f"{local_prefix}:{abbrev_term}"] = term

    # read the diagram and retrieve relationships
    diagram = ReadDiagram(INPUT_PATH)
    rels = diagram.get_relationships()

    g = nx.DiGraph()
    # parse the elements, parse their prefixes, and set as URI
    terms = dict()
    class_terms = set()
    predicate_terms = set()

    substituted_terms = []
    used_prefixes = set()
    for _, row in rels.iterrows():
        parent, child, rel = (
            row["parent"],
            row["child"],
            row["rel"]
        )

        term_items = [parent, child, rel]
        for idx, term in enumerate(term_items):
            if ":" in term:
                prefix, abbrev_term = term.split(":")
            else:
                prefix = None
                abbrev_term = term

            if prefix is None:
                ns_uri = prefixes["mds"]
            elif prefix not in prefixes:
                raise KeyError(
                    f"Cannot find prefix {prefix} in prefix master list. Consider adding it."
                )
            else:
                ns_uri = prefixes[prefix]

            # add used prefix to set of used prefixes to bind later
            used_prefixes.add(inv_prefixes[str(ns_uri)])

            # if the term is a predicate, replace underscores with spaces and enforce lowercase start
            strict_camel_case = False
            if idx == len(term_items) - 1:
                abbrev_term = abbrev_term.replace("_", " ")
                strict_camel_case = True

            abbrev_term = "".join(
                [
                    f"{word[0].upper()}{word[1:] if len(word) > 1 else ''}"
                    for word in abbrev_term.split()
                ]
            )

            if strict_camel_case and term[0].islower():
                abbrev_term = f"{abbrev_term[0].lower()}{abbrev_term[1:] if len(abbrev_term) > 1 else ''}"

            term_uri = rdflib.URIRef(f"{ns_uri}{abbrev_term}")

            # TODO: potentially add a key for a new term, i.e. *
            if prefix in prefixes and "*" not in term:
                sub = process.extractOne(
                    f"{prefix}:{abbrev_term}",
                    search_terms.keys(),
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=80
                    # TODO: determine an ideal cutoff for terms
                    # TODO: output substituted terms to the user to verify if within the warning
                )
                if sub:
                    term_key, score = sub
                    term_uri = search_terms[term_key]
                    # print(f"{term} -> {term_key} ({score})")
                    substituted_terms.append((term, term_key, score))

            terms[term] = term_uri

        # add relationships to the graph
        predicate_terms.add(terms[rel])

        g.add_edge(terms[parent], terms[child], label=terms[rel])
    # iterate through all subclass of relations
    for parent, child, data in g.edges(data=True):
        predicate = data['label']

        if predicate == RDFS.subClassOf:
            class_terms.update([parent, child])

        if predicate == RDF.type:
            class_terms.add(child)

    # create an rdf graph
    rdf_graph = rdflib.Graph()

    # bind prefixes to namespaces
    for prefix in used_prefixes:
        rdf_graph.bind(prefix, prefixes[prefix])

    # TODO: collect edge inputs and outputs on custom properties, assume union of terms for now, fix later
    predicate_domain = defaultdict(list)
    predicate_range = defaultdict(list)
    for domain_term, range_term, data in g.edges(data=True):
        predicate_term = data["label"]
        predicate_domain[predicate_term].append(domain_term)
        predicate_range[predicate_term].append(range_term)

    # combine node and edge objects into one collection of terms
    all_edges = {data['label'] for _, _, data in g.edges(data=True)}
    all_nodes = g.nodes() | all_edges

    # add term types and exact matches if any
    for node in all_nodes:
        ns, abbrev_term = split_uri(node)
        prefix = inv_prefixes[str(ns)]
        search_term = f"{prefix}:{abbrev_term}"

        if node in class_terms:
            rdf_graph.add((node, RDF.type, OWL.Class))
        
        if prefix not in default_namespace_prefixes:
            if node in predicate_terms:
                # TODO: Assume all predicates are object properties for now, change later
                rdf_graph.add((node, RDF.type, OWL.ObjectProperty))

            if search_term in search_terms:
                exact_term = search_terms[search_term]
                term_type = search_term_onto_graph.value(exact_term, RDF.type)
                label = search_term_onto_graph.value(exact_term, RDFS.label)
                
                if term_type:
                    rdf_graph.add((node, RDF.type, term_type))

                if label:
                    rdf_graph.add((node, RDFS.label, label))

                rdf_graph.add((node, SKOS.exactMatch, exact_term))
            elif node in predicate_terms:
                # add domains and ranges for the object property
                for dom_or_range_term, node_dom_range in {
                    RDFS.domain: predicate_domain[node],
                    RDFS.range: predicate_range[node],
                }.items():
                    if node_dom_range:
                        if len(node_dom_range) > 1:
                            collection_node = rdflib.BNode()
                            collection_list = Collection(
                                rdf_graph, collection_node, node_dom_range
                            )
                            # create class that points to the collection
                            collection_class = rdflib.BNode()
                            rdf_graph.add((collection_class, RDF.type, OWL.Class))
                            # connect them all together
                            rdf_graph.add(
                                (collection_class, OWL.unionOf, collection_node)
                            )
                            rdf_graph.add((node, dom_or_range_term, collection_class))

    # now add the triples inside the diagram
    for domain_term, range_term, data in g.edges(data=True):
        predicate_term = data["label"]
        rdf_graph.add((domain_term, predicate_term, range_term)) 
    # serialize the output as a turtle file
    rdf_graph.serialize('output.ttl')

    # evaluate output by converting back to drawio
    ex = ReadTurtle('output.ttl')
    graph = ex.get_graph()
    tree = Tree(graph=ex.get_graph(), do_gen_ids=True)
    diagram = WriteDiagram('output.drawio')
    tree.draw_tree(write_diagram=diagram)
    diagram.draw()
