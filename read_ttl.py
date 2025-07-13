import rdflib
from collections import defaultdict
from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS
from rdflib.namespace import split_uri
import networkx as nx
from cemento.tree import Tree
from cemento.draw_io.write_diagram import WriteDiagram

INPUT_PATH = "/srv/samba-share/mds/mds-onto/CEMENTO/sandbox/output.ttl"

if __name__ == "__main__":
    rdf_graph = rdflib.Graph()
    rdf_graph.parse(INPUT_PATH, format='turtle')

    prefixes = {prefix: ns for prefix, ns in rdf_graph.namespaces()}

    default_namespaces = [RDF, RDFS, OWL, DCTERMS, SKOS]
    default_namespace_prefixes = ["rdf", "rdfs", "owl", "dcterms", "skos"]

    prefixes.update({prefix:ns for prefix, ns in zip(default_namespace_prefixes, default_namespaces)})
    inv_prefix = {str(value): key for key, value in prefixes.items()}

    default_terms = {term for ns in default_namespaces for term in dir(ns) if isinstance(term, rdflib.URIRef)}

    all_classes, all_instances = set(), set()
    aliases = defaultdict(list)

    term_type = dict()

    for subj, pred, obj in rdf_graph:
        if pred == RDFS.subClassOf:
            all_classes.update([subj, obj])
        
        if pred == RDF.type:
            term_type[subj] = obj
        
        if pred == RDFS.label or pred == SKOS.altLabel:
            aliases[subj].append(obj)
    
    for subj, pred, obj in rdf_graph:
        if pred == RDF.type and obj not in default_terms and term_type[obj] == OWL.Class:
            all_classes.add(subj)
            all_instances.add(obj)
    
    all_predicates = {term for term in rdf_graph.subjects(RDF.type, OWL.ObjectProperty) if term not in default_terms}
    all_predicates.add(RDF.type)
    all_predicates.add(RDFS.subClassOf)
    all_terms = all_classes | all_predicates | all_instances

    rename_terms = dict()
    for term in all_terms | default_terms:
        ns, abbrev_term = split_uri(term)
        prefix = inv_prefix[ns]
        new_name = f"{prefix}:{abbrev_term}"
        if aliases[term]:
            if term in all_classes or term in all_instances:
                new_name += f" ({','.join(aliases[term])})"
            else:
                new_name = f"{prefix}:{aliases[term][0]}"
        rename_terms[term] = new_name
    
    graph = nx.DiGraph()
    for subj, pred, obj in rdf_graph:
        if pred in all_predicates and subj not in default_terms and obj not in default_terms:
            is_rank = pred == RDF.type or pred == RDFS.subClassOf
            graph.add_edge(obj, subj, label=rename_terms[pred], is_rank=is_rank)
    
    graph = nx.relabel_nodes(graph, rename_terms)
    for parent, child, data in graph.edges(data=True):
        print(parent, child, data['label'])
    tree = Tree(graph=graph, do_gen_ids=True, invert_tree=False)
    diagram = WriteDiagram('sample.drawio')
    tree.draw_tree(write_diagram=diagram)
    diagram.draw()