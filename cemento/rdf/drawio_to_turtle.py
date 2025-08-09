from pathlib import Path

from cemento.draw_io.read_diagram import read_drawio
from cemento.rdf.graph_to_turtle import convert_graph_to_ttl


def convert_drawio_to_ttl(
    input_path: str | Path,
    output_path: str | Path,
    onto_ref_folder: str | Path = None,
    defaults_folder: str | Path = None,
    prefixes_path: str | Path = None,
    check_errors: bool = False,
    collect_domains_ranges: bool = False,
    log_substitution_path: str | Path = None,
) -> None:
    """
    Convert an input draw.io diagram file of an ontology into RDF triples in the turtle format.

    Args:
        input_path (str | Path): The path to the draw.io file input.
        output_path (str | Path): The desired file path for saving the RDF triples in the turtle format.
        onto_ref_folder (str | Path): The path to the folder containing the reference ontologies.
        defaults_folder (str | Path): The path to the folder containing the turtle files of the default namespaces.
        prefixes_path (str | Path): The path to the json file containing prefixes.
        log_substitution_path (str | Path, optional): The path to a csv file containing substitution results from term matching. Defaults to **None**.

    Returns:
        None
    """
    graph = read_drawio(
        input_path,
        onto_ref_folder=onto_ref_folder,
        prefixes_file=prefixes_path,
        defaults_folder=defaults_folder,
        check_errors=check_errors,
    )
    convert_graph_to_ttl(
        graph,
        output_path,
        onto_ref_folder=onto_ref_folder,
        collect_domains_ranges=collect_domains_ranges,
        defaults_folder=defaults_folder,
        prefixes_path=prefixes_path,
        log_substitution_path=log_substitution_path,
    )
