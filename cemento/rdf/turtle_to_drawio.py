from pathlib import Path

from cemento.draw_io.write_diagram import draw_tree
from cemento.rdf.turtle_to_graph import convert_ttl_to_graph


def convert_ttl_to_drawio(
    input_path: str | Path, output_path: str | Path, horizontal_tree: bool = False
):
    graph = convert_ttl_to_graph(input_path)
    draw_tree(graph, output_path, horizontal_tree=horizontal_tree)
