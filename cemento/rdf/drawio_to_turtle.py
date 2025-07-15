from cemento.draw_io.read_diagram import read_drawio
from pathlib import Path
from cemento.rdf.graph_to_turtle import convert_graph_to_ttl

def convert_drawio_to_ttl(
    file_path: str | Path,
    output_path: str | Path,
    onto_ref_folder: str | Path,
    prefixes_path: str | Path,
):
    convert_graph_to_ttl(
        read_drawio(file_path), output_path, onto_ref_folder, prefixes_path
    )