from collections import defaultdict
from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS, Graph, URIRef, Literal
from rdflib.namespace import split_uri
import networkx as nx
from networkx import DiGraph
from cemento.tree import Tree
from cemento.draw_io.write_diagram import WriteDiagram
from contextlib import contextmanager

INPUT_PATH = "/Users/gabriel/dev/sdle/CEMENTO/sandbox/output.ttl"

@contextmanager
def read_ttl(file_path: str) -> Graph:
    rdf_graph = Graph()
    try:
        rdf_graph.parse(INPUT_PATH, format='turtle')
        yield rdf_graph
    finally:
        rdf_graph.close()

def get_aliases(rdf_graph: Graph) -> dict[URIRef, Literal]:
    aliases = defaultdict(list)
    for subj, pred, obj in rdf_graph:
        if pred == RDFS.label or pred == SKOS.altLabel:
            aliases[subj].append(obj)

    return aliases

def get_term_types(rdf_graph: Graph) -> dict[URIRef, URIRef]:
    term_type = dict()
    for subj, pred, obj in rdf_graph:
        if pred == RDF.type:
            term_type[subj] = obj

    return term_type

def get_terms(rdf_graph: Graph, term_type: dict[URIRef, URIRef]) -> tuple[set[URIRef], set[URIRef], set[URIRef]]:
    all_classes, all_instances = set(), set()

    for subj, pred, obj in rdf_graph:
        if pred == RDFS.subClassOf:
            all_classes.update([subj, obj])
    
    for subj, pred, obj in rdf_graph:
        if pred == RDF.type and obj not in default_terms and term_type[obj] == OWL.Class:
            all_classes.add(subj)
            all_instances.add(obj)
    
    all_predicates = {term for term in rdf_graph.subjects(RDF.type, OWL.ObjectProperty) if term not in default_terms}
    all_predicates.add(RDF.type)
    all_predicates.add(RDFS.subClassOf)

    return all_classes, all_instances, all_predicates

def get_graph_relabel_mapping(terms: URIRef, aliases: dict[URIRef, Literal]) -> dict[URIRef, str]:
    rename_mapping = dict()
    for term in terms:
        ns, abbrev_term = split_uri(term)
        prefix = inv_prefix[ns]
        new_name = f"{prefix}:{abbrev_term}"
        if aliases[term]:
            if term in all_classes or term in all_instances:
                new_name += f" ({','.join(aliases[term])})"
            else:
                new_name = f"{prefix}:{aliases[term][0]}"
        rename_mapping[term] = new_name
    return rename_mapping

def get_graph(rdf_graph: Graph, all_predicates: set[URIRef], default_terms: set[URIRef]) -> DiGraph:
    graph = DiGraph()
    for subj, pred, obj in rdf_graph:
        if pred in all_predicates and subj not in default_terms and obj not in default_terms:
            is_rank = pred == RDF.type or pred == RDFS.subClassOf
            graph.add_edge(obj, subj, label=pred, is_rank=is_rank)
    return graph

def rename_edges(graph: DiGraph, rename_mapping: dict[URIRef, str]) -> DiGraph:
    edge_rename_mapping = dict()
    graph = graph.copy()
    for subj, obj, data in graph.edges(data=True):
        pred = data['label']
        print(pred)
        new_edge_label = rename_mapping[pred]
        edge_rename_mapping[(subj, obj)] = {'label': new_edge_label}
    nx.set_edge_attributes(graph, edge_rename_mapping)
    return graph

if __name__ == "__main__":
    default_namespaces = [RDF, RDFS, OWL, DCTERMS, SKOS]
    default_namespace_prefixes = ["rdf", "rdfs", "owl", "dcterms", "skos"]

    with read_ttl(INPUT_PATH) as rdf_graph:

        prefixes = {prefix: ns for prefix, ns in rdf_graph.namespaces()}
        prefixes.update({prefix:ns for prefix, ns in zip(default_namespace_prefixes, default_namespaces)})

        inv_prefix = {str(value): key for key, value in prefixes.items()}

        default_terms = {term for ns in default_namespaces for term in dir(ns) if isinstance(term, URIRef)}

        term_type = get_term_types(rdf_graph)
        all_classes, all_instances, all_predicates = get_terms(rdf_graph, term_type)
    
        graph = get_graph(rdf_graph, all_predicates, default_terms)

        all_terms = all_classes | all_instances | all_predicates | default_terms
        aliases = get_aliases(rdf_graph)
        rename_terms = get_graph_relabel_mapping(all_terms, aliases)
        graph = nx.relabel_nodes(graph, rename_terms)
        graph = rename_edges(graph, rename_terms)

    tree = Tree(graph=graph, do_gen_ids=True, invert_tree=False)
    diagram = WriteDiagram('sample.drawio')
    tree.draw_tree(write_diagram=diagram)
    diagram.draw()