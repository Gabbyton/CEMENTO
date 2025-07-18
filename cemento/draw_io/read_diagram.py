from pathlib import Path

from networkx import DiGraph

from cemento.draw_io.constants import DiagramKey
from cemento.draw_io.transforms import (
    extract_elements,
    generate_graph,
    parse_elements,
    relabel_graph_nodes_with_node_attr,
)
from cemento.term_matching.transforms import get_prefixes, get_strat_predicates_str


def read_drawio(
    input_path: str | Path,
    onto_ref_folder: str | Path,
    prefixes_folder: str | Path,
    defaults_folder: str | Path,
    relabel_key: DiagramKey = DiagramKey.LABEL,
    inverted_rank_arrow: bool = False,
) -> DiGraph:
    elements = parse_elements(input_path)
    term_ids, rel_ids = extract_elements(elements)
    # add annotation terms to set for checking
    # TODO: add backup constant terms if any of the ref folders are not set
    prefixes, inv_prefixes = get_prefixes(prefixes_folder, onto_ref_folder)
    strat_props = get_strat_predicates_str(
        onto_ref_folder, defaults_folder, inv_prefixes
    )
    graph = generate_graph(
        elements,
        term_ids,
        rel_ids,
        strat_props,
        inverted_rank_arrow=inverted_rank_arrow,
    )
    graph = relabel_graph_nodes_with_node_attr(graph, new_attr_label=relabel_key.value)
    return graph
