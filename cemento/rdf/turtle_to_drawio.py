from pathlib import Path

from cemento.draw_io.write_diagram import draw_tree
from cemento.rdf.turtle_to_graph import convert_ttl_to_graph


def convert_ttl_to_drawio(
    input_path: str | Path,
    output_path: str | Path,
    horizontal_tree: bool = False,
    onto_ref_folder: str | Path = None,
    defaults_folder: str | Path = None,
    prefixes_path: str | Path = None,
    check_ttl_validity: bool = True,
    set_unique_literals: bool = True,
):
    graph = convert_ttl_to_graph(
        input_path,
        onto_ref_folder=onto_ref_folder,
        defaults_folder=defaults_folder,
        prefixes_path=prefixes_path,
        check_ttl_validity=check_ttl_validity,
        set_unique_literals=set_unique_literals,
    )
    draw_tree(graph, output_path, horizontal_tree=horizontal_tree)
