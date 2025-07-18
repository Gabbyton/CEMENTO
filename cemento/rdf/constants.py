from rdflib import OWL

PREDICATES = {OWL.ObjectProperty, OWL.AnnotationProperty, OWL.DatatypeProperty}

DEFAULT_DOWNLOADS = {
    # cco as the default download
    "cco": "https://raw.githubusercontent.com/CommonCoreOntology/CommonCoreOntologies/refs/heads/develop/src/cco-merged/CommonCoreOntologiesMerged.ttl"
}
