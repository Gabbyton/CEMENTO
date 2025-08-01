from pathlib import Path

from cemento.draw_io.write_diagram import draw_tree
from cemento.rdf.turtle_to_graph import convert_ttl_to_graph


def convert_ttl_to_drawio(
    input_path: str | Path,
    output_path: str | Path,
    horizontal_tree: bool = False,
    classes_only: bool = False,
    demarcate_boxes: bool = False,
    onto_ref_folder: str | Path = None,
    defaults_folder: str | Path = None,
    prefixes_path: str | Path = None,
    set_unique_literals: bool = True,
) -> None:
    graph = convert_ttl_to_graph(
        input_path,
        classes_only=classes_only,
        onto_ref_folder=onto_ref_folder,
        defaults_folder=defaults_folder,
        prefixes_path=prefixes_path,
        set_unique_literals=set_unique_literals,
    )
    draw_tree(
        graph,
        output_path,
        classes_only=classes_only,
        demarcate_boxes=demarcate_boxes,
        horizontal_tree=horizontal_tree,
    )
