from pathlib import Path

from networkx import DiGraph

from cemento.draw_io.constants import DiagramKey
from cemento.draw_io.transforms import (
    extract_elements,
    generate_graph,
    parse_elements,
    relabel_graph_nodes,
)


def read_drawio(
    input_path: str | Path,
    relabel_key: DiagramKey = DiagramKey.LABEL,
    inverted_rank_arrow: bool = False,
) -> DiGraph:
    elements = parse_elements(input_path)
    term_ids, rel_ids = extract_elements(elements)
    rank_terms = ["rdfs:subClassOf", "rdf:type"]
    annotation_terms = []
    graph = generate_graph(
        elements,
        term_ids,
        rel_ids,
        rank_terms,
        annotation_terms,
        inverted_rank_arrow=inverted_rank_arrow,
    )
    graph = relabel_graph_nodes(graph, new_attr_label=relabel_key.value)
    return graph
