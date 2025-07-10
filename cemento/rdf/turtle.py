import rdflib
from rdflib.namespace import split_uri
from cemento.graph import Graph
import networkx as nx
from collections import defaultdict
import pandas as pd
import numpy as np

class Turtle(Graph):

    def __init__(self, file_path):
        super().__init__(file_path, rels_df=None, graph=None, ref=None, do_gen_ids=True, infer_rank=False)
        self._file_path = file_path
        self._rdf_graph = None
        self._rename_vars = defaultdict(list)
        self._prefixes = dict()

        # parse ttl file into graph
        self._rdf_graph = rdflib.Graph()
        self._rdf_graph.parse(self._file_path, format='turtle')

        # read through namespaces and store prefixes
        self._prefixes = {str(value): key for key, value in self._rdf_graph.namespaces()}

        # get all accepted terms, object properties and classes

        class_terms = set()
        subclass_triples = []
        object_prop_triples = defaultdict(list)
        term_type = defaultdict(list)
        for subj, pred, obj in self._rdf_graph:
            if pred == rdflib.RDFS.subClassOf and isinstance(subj, rdflib.URIRef) and isinstance(obj, rdflib.URIRef):
                subclass_triples.append((subj, obj))
                class_terms.update([subj, obj])
            
            if pred == rdflib.RDF.type:
                term_type[obj].append(subj)

            if pred == rdflib.RDFS.label:
                self._rename_vars[subj].insert(0, obj)
            
            if pred == rdflib.SKOS.altLabel:
                self._rename_vars[subj].append(obj) 
        
        for obj_prop in term_type[rdflib.OWL.ObjectProperty]:
            for prop_subj, prop_pred, prop_obj in self._rdf_graph.triples((None, obj_prop, None)):
                if isinstance(prop_subj, rdflib.URIRef) and isinstance(prop_obj, rdflib.URIRef):
                    object_prop_triples[prop_pred].append((subj, obj))
        
        all_classes = {term for term in self._rdf_graph.subjects(rdflib.RDF.type, rdflib.OWL.Class) if isinstance(term, rdflib.URIRef)}
        class_terms.update(all_classes - class_terms)
        
        self._graph = nx.DiGraph()
        self._graph.add_edges_from(subclass_triples, label="rdfs:subClassOf")
        for pred, triples in object_prop_triples.items():
            self._graph.add_edges_from(triples, label=self.get_abbrev_name(pred))
        self._graph.add_nodes_from(class_terms)

        new_term_names = dict()
        for term in all_classes:
            all_names = self.get_all_names(term)
            extra_name = f" ({','.join(all_names)})"
            new_term_names[term] = f"{self.get_abbrev_name(term)}{extra_name if all_names else ''}"
        # print(new_term_names)
        self._graph = nx.relabel_nodes(self._graph, new_term_names)

        # get edge data
        df_triples = [(parent, child, data['label']) for parent, child, data in self._graph.edges(data=True)]
        self._rels_df = pd.DataFrame(np.array(df_triples), columns=['parent', 'child', 'rel'])
       
    def get_rdf_graph(self):
        return self._rdf_graph

    def get_prefix(self, uri):
        return self._prefixes[uri]
    
    def _get_rename_vars(self):
        return self._rename_vars

    def get_abbrev_name(self, term):
        uri, abbrev_name = split_uri(term)
        prefix = self.get_prefix(uri)
        abbrev_name = f"{prefix}:{abbrev_name}"
        return abbrev_name

    def get_common_name(self, term):
        try:
            rename_vars = self._get_rename_vars()
            return rename_vars[term][0]
        except (IndexError, KeyError):
            return term
    
    def get_all_names(self, term):
        return self._rename_vars[term]