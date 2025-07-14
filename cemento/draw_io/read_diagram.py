from pathlib import Path

import networkx as nx
from networkx import DiGraph
from thefuzz import process

from cemento.draw_io.constants import DiagramKey
from cemento.draw_io.preprocessing import clean_term
from cemento.draw_io.transforms import extract_elements, parse_elements


def generate_graph(
    elements: dict[str, dict[str, any]],
    term_ids: set[str],
    relationship_ids: set[str],
    rank_terms: set[str],
    inverted_rank_arrow: bool = False,
) -> DiGraph:
    # for identified connectors, extract relationship information
    graph = nx.DiGraph()
    # add all terms
    for term_id in term_ids:
        term = elements[term_id]["value"]
        graph.add_node(term_id, term_id=term_id, label=clean_term(term))

    # add all relationships
    for rel_id in relationship_ids:
        subj_id = elements[rel_id]["source"]
        obj_id = elements[rel_id]["target"]
        pred = clean_term(elements[rel_id]["value"])

        matched_rank_pred, score = process.extractOne(
            pred.lower(), [rank_term.lower() for rank_term in rank_terms]
        )
        is_rank = score > 85
        pred = matched_rank_pred if is_rank else pred

        # arrow conventions are inverted for rank relationships, flip assignments to conform
        if inverted_rank_arrow and is_rank:
            temp = subj_id
            subj_id = obj_id
            obj_id = temp

        graph.add_edge(
            subj_id,
            obj_id,
            label=pred,
            pred_id=rel_id,
            is_rank=is_rank,
            is_predicate=True,
        )

    return graph


def relabel_graph_nodes(
    graph: DiGraph, new_attr_label=DiagramKey.TERM_ID.value
) -> DiGraph:
    node_info = nx.get_node_attributes(graph, new_attr_label)
    relabel_mapping = {
        current_node_label: node_info[current_node_label]
        for current_node_label in graph.nodes
    }
    return nx.relabel_nodes(graph, relabel_mapping)


def read_drawio(
    input_path: str | Path,
    relabel_key: DiagramKey = DiagramKey.LABEL,
    inverted_rank_arrow: bool = False,
) -> DiGraph:
    elements = parse_elements(input_path)
    term_ids, rel_ids = extract_elements(elements)
    rank_terms = ["rdfs:subClassOf", "rdf:type"]
    graph = generate_graph(
        elements, term_ids, rel_ids, rank_terms, inverted_rank_arrow=inverted_rank_arrow
    )
    graph = relabel_graph_nodes(graph, new_attr_label=relabel_key.value)
    return graph
