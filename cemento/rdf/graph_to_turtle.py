from copy import deepcopy
from functools import partial, reduce
from itertools import filterfalse
from pathlib import Path

import networkx as nx
import rdflib
from networkx import DiGraph
from rdflib import OWL, RDF, RDFS

from cemento.rdf.filters import term_in_search_results, term_not_in_default_namespace
from cemento.rdf.io import (
    get_diagram_terms_iter,
    get_diagram_terms_iter_with_pred,
)
from cemento.rdf.preprocessing import (
    get_term_aliases,
)
from cemento.rdf.transforms import (
    add_domains_ranges,
    add_labels,
    add_rdf_triples,
    bind_prefixes,
    construct_literal,
    construct_term_uri,
    get_class_terms,
    get_domains_ranges,
    get_literal_data_type,
    get_literal_lang_annotation,
    get_term_value,
    substitute_term,
)
from cemento.term_matching.constants import get_default_namespace_prefixes
from cemento.term_matching.io import get_ttl_file_iter
from cemento.term_matching.transforms import (
    add_exact_matches,
    combine_graphs,
    get_prefixes,
    get_search_terms,
    get_term_search_keys,
    get_term_types,
)
from cemento.utils.utils import fst, get_abbrev_term, snd


def convert_graph_to_ttl(
    graph: DiGraph,
    output_path: str | Path,
    onto_ref_folder: str | Path = None,
    prefixes_path: str | Path = None,
) -> None:
    prefixes, inv_prefixes = get_prefixes(prefixes_path, onto_ref_folder)
    search_terms = get_search_terms(inv_prefixes, onto_ref_folder)

    aliases = {
        term: aliases
        for term, aliases in map(
            lambda term: (term, get_term_aliases(term)), get_diagram_terms_iter(graph)
        )
    }

    literal_terms = {
        term
        for term in filter(lambda term: ('"' in term), get_diagram_terms_iter(graph))
    }
    try:
        constructed_terms = {
            term: term_uri_ref
            for term, term_uri_ref in map(
                lambda term_info: (
                    fst(term_info),
                    construct_term_uri(
                        *get_abbrev_term(fst(term_info), snd(term_info)),
                        prefixes=prefixes,
                    ),
                ),
                filter(
                    lambda term_info: fst(term_info) not in literal_terms,
                    get_diagram_terms_iter_with_pred(graph),
                ),
            )
        }
    except KeyError as e:
        offending_key = e.args[0]
        if prefixes_path:
            raise ValueError(
                f"The prefix {offending_key} was used but it was not in the prefix.json file located in {prefixes_path}. Please consider adding it there."
            ) from KeyError
        else:
            raise ValueError(
                f"The prefix {offending_key} was used but it is not part of the default namespace. Consider creating a prefixes.json file and add set the prefixes_path argument."
            ) from KeyError
    search_keys = {
        term: search_key
        for term, search_key in map(
            lambda term: (term, get_term_search_keys(term, inv_prefixes)),
            get_diagram_terms_iter(graph),
        )
    }
    substitution_results = {
        term: substituted_value
        for term, substituted_value in map(
            lambda term: (term, substitute_term(search_keys[term], search_terms)),
            get_diagram_terms_iter(graph),
        )
        if substituted_value is not None
    }

    inv_constructed_terms = {value: key for key, value in constructed_terms.items()}

    constructed_terms.update(substitution_results)
    constructed_literal_terms = {
        term: construct_literal(
            term,
            lang=get_literal_lang_annotation(term),
            datatype=get_literal_data_type(term, search_terms),
        )
        for term in literal_terms
    }
    constructed_terms.update(constructed_literal_terms)

    output_graph = nx.DiGraph()
    for subj, obj, data in graph.edges(data=True):
        pred = data["label"]
        subj, obj, pred = tuple(constructed_terms[key] for key in (subj, obj, pred))
        output_graph.add_edge(subj, obj, label=pred)

    class_terms = get_class_terms(output_graph)
    predicate_terms = {data["label"] for _, _, data in output_graph.edges(data=True)}
    literal_terms = set(constructed_literal_terms.values())
    class_terms -= predicate_terms
    all_terms = (output_graph.nodes() | predicate_terms) - literal_terms

    # # create the rdf graph to store the ttl output
    rdf_graph = rdflib.Graph()

    # bind prefixes to namespaces for the rdf graph
    rdf_graph = bind_prefixes(rdf_graph, prefixes)

    # add all of the class terms as a type
    rdf_graph = add_rdf_triples(
        rdf_graph, ((term, RDF.type, OWL.Class) for term in class_terms)
    )

    # if the term is a predicate and is not part of the default namespaces, add an object property type to the ttl file
    ref_graph = deepcopy(rdf_graph)
    if onto_ref_folder:
        ref_graph += combine_graphs(get_ttl_file_iter(onto_ref_folder))
    term_types = get_term_types(ref_graph)

    term_not_in_default_namespace_filter = partial(
        term_not_in_default_namespace,
        inv_prefixes=inv_prefixes,
        default_namespace_prefixes=get_default_namespace_prefixes(),
    )
    term_type_subs = {
        key: value
        for key, value in map(
            lambda term: (
                term,
                term_types[term] if term in term_types else OWL.ObjectProperty,
            ),
            filter(term_not_in_default_namespace_filter, predicate_terms),
        )
    }
    # Assume a custom property is just a property
    # TODO: Add default schema files for rdf, rdfs and owl to get default namespace terms
    rdf_graph = add_rdf_triples(
        rdf_graph,
        (
            (term, RDF.type, term_type_subs[term])
            for term in filter(term_not_in_default_namespace_filter, predicate_terms)
        ),
    )

    term_in_search_results_filter = partial(
        term_in_search_results, inv_prefixes=inv_prefixes, search_terms=search_terms
    )

    if onto_ref_folder:
        exact_match_property_predicates = [RDF.value, RDFS.label]
        exact_match_properties = {
            term: {prop: value}
            for prop in exact_match_property_predicates
            for result in map(
                lambda rdf_graph, prop=prop: map(
                    lambda graph_term: (
                        graph_term,
                        get_term_value(
                            subj=graph_term, pred=prop, ref_rdf_graph=ref_graph
                        ),
                    ),
                    all_terms,
                ),
                get_ttl_file_iter(onto_ref_folder),
            )
            for term, value in result
        }
        rdf_graph = reduce(
            lambda rdf_graph, graph_term: add_exact_matches(
                term=graph_term,
                match_properties=exact_match_properties[graph_term],
                rdf_graph=rdf_graph,
            ),
            filter(
                term_in_search_results_filter,
                filter(term_not_in_default_namespace_filter, all_terms),
            ),
            rdf_graph,
        )
    rdf_graph = reduce(
        lambda rdf_graph, graph_term: add_labels(
            term=graph_term,
            labels=aliases[inv_constructed_terms[graph_term]],
            rdf_graph=rdf_graph,
        ),
        filter(
            term_not_in_default_namespace_filter,
            filterfalse(term_in_search_results_filter, all_terms),
        ),
        rdf_graph,
    )
    predicate_domains_ranges = map(
        partial(get_domains_ranges, graph=output_graph),
        filter(
            term_not_in_default_namespace_filter,
            filterfalse(term_in_search_results_filter, predicate_terms),
        ),
    )
    rdf_graph = reduce(
        lambda rdf_graph, triples: add_domains_ranges(triples, rdf_graph),
        predicate_domains_ranges,
        rdf_graph,
    )

    # now add the triples from the drawio diagram
    for domain_term, range_term, data in output_graph.edges(data=True):
        predicate_term = data["label"]
        rdf_graph.add((domain_term, predicate_term, range_term))
    # serialize the output as a turtle file
    rdf_graph.serialize(output_path)
