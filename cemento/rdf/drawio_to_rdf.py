from pathlib import Path

from cemento.draw_io.read_diagram import read_drawio
from cemento.rdf.graph_to_rdf import convert_graph_to_rdf


def convert_drawio_to_rdf(
    input_path: str | Path,
    output_path: str | Path,
    onto_ref_folder: str | Path = None,
    defaults_folder: str | Path = None,
    prefixes_path: str | Path = None,
    check_errors: bool = False,
    collect_domains_ranges: bool = False,
    log_substitution_path: str | Path = None,
) -> None:
    graph = read_drawio(
        input_path,
        onto_ref_folder=onto_ref_folder,
        prefixes_file=prefixes_path,
        defaults_folder=defaults_folder,
        check_errors=check_errors,
    )
    convert_graph_to_rdf(
        graph,
        output_path,
        onto_ref_folder=onto_ref_folder,
        collect_domains_ranges=collect_domains_ranges,
        defaults_folder=defaults_folder,
        prefixes_path=prefixes_path,
        log_substitution_path=log_substitution_path,
    )
