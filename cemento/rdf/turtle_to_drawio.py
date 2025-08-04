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
    set_unique_literals: bool = False,
) -> None:
    """
    Convert RDF triples in the turtle format as an ontology diagram in a draw.io file.

    Args:
        input_path (str | Path): The path to the turtle input file.
        output_path (str | Path): The desired file path for saving an ontology diagram as a draw.io file.
        horizontal_tree (bool, optional): Whether to make the tree horizontal or stay with the default vertical layout. Defaults to **False**.
        classes_only (bool, optional): Whether to just display classes and instances (taxonomy tree). Defaults to **False**.
        onto_ref_folder (str | Path, optional): The path to the folder containing the reference ontologies. Defaults to **None**.
        defaults_folder (str | Path, optional): The path to the folder containing the turtle files of the default namespaces. Defaults to **None**.
        prefixes_path (str | Path, optional): The path to the json file containing prefixes. Defaults to **None**.
        log_substitution_path (str | Path, optional): The path to a csv file containing substitution results from term matching. Defaults to **None**.

    Returns:
        None
    """
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
