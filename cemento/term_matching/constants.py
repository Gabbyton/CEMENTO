from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS

default_namespaces = [RDF, RDFS, OWL, DCTERMS, SKOS]
default_namespace_prefixes = ["rdf", "rdfs", "owl", "dcterms", "skos"]


def get_default_namespace_prefixes():
    return {
        prefix: ns
        for prefix, ns in zip(
            default_namespace_prefixes, default_namespaces, strict=True
        )
    }
