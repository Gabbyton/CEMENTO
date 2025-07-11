import rdflib
from cemento.rdf.turtle import Turtle

class WriteTurtle(Turtle):
    
    # TODO: move away from unreliable triples and switch to graph and the fundamental object
    def __init__(self, file_output_path, prefixes, graph):
        super().__init__(file_path=file_output_path, graph=graph, prefixes=prefixes)

        self._rdf_graph = rdflib.Graph()
        namespaces = dict()
        
        # bind namespaces and save to a dictionary
        for url, prefix in prefixes:
            ns = rdflib.Namespace(url)
            self._rdf_graph.bind(prefix, ns)
            namespaces[prefix] = ns
        
        # TODO: parse draw io diagram with termID (name, altnames**)
        # TODO: parse object property relations in a separate page
        # TODO: parse definitions through a separate page, auto-generate/auto-populate if new terms are added