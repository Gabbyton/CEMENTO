from collections import defaultdict

import networkx as nx
import rdflib

from cemento.rdf.turtle import Turtle


class ReadTurtle(Turtle):

    def __init__(self, file_path, include_labels=True):
        super().__init__(file_path=file_path)

        # parse ttl file into graph
        self._rdf_graph = rdflib.Graph()
        self._rdf_graph.parse(self._file_path, format="turtle")

        # read through namespaces and store prefixes
        self._prefixes = {
            str(value): key for key, value in self._rdf_graph.namespaces()
        }

        # get all accepted terms, object properties and classes

        class_terms = set()
        subclass_triples = []
        object_prop_triples = defaultdict(list)
        term_type = defaultdict(list)
        for subj, pred, obj in self._rdf_graph:
            if (
                pred == rdflib.RDFS.subClassOf
                and isinstance(subj, rdflib.URIRef)
                and isinstance(obj, rdflib.URIRef)
            ):
                subclass_triples.append((obj, subj))
                class_terms.update([subj, obj])

            if pred == rdflib.RDF.type:
                term_type[obj].append(subj)

            if pred == rdflib.RDFS.label:
                self._rename_vars[subj].insert(0, obj)

            if pred == rdflib.SKOS.altLabel:
                self._rename_vars[subj].append(obj)

        for obj_prop in term_type[rdflib.OWL.ObjectProperty]:
            for prop_subj, prop_pred, prop_obj in self._rdf_graph.triples(
                (None, obj_prop, None)
            ):
                if isinstance(prop_subj, rdflib.URIRef) and isinstance(
                    prop_obj, rdflib.URIRef
                ):
                    object_prop_triples[prop_pred].append((subj, obj))

        all_classes = {
            term
            for term in self._rdf_graph.subjects(rdflib.RDF.type, rdflib.OWL.Class)
            if isinstance(term, rdflib.URIRef)
        }
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
            new_term_names[term] = (
                f"{self.get_abbrev_name(term)}{extra_name if include_labels and all_names else ''}"
            )
        self._graph = nx.relabel_nodes(self._graph, new_term_names)
