from pathlib import Path

from cemento.draw_io.read_diagram import read_drawio
from cemento.rdf.graph_to_turtle import convert_graph_to_ttl


def convert_drawio_to_ttl(
    file_path: str | Path,
    output_path: str | Path,
    onto_ref_folder: str | Path,
    defaults_folder: str | Path,
    prefixes_path: str | Path,
    log_substitution_path: str | Path = None,
) -> None:
    graph = read_drawio(file_path, onto_ref_folder, prefixes_path, defaults_folder)
    convert_graph_to_ttl(
        graph,
        output_path,
        onto_ref_folder,
        prefixes_path,
        log_substitution_path=log_substitution_path,
    )
