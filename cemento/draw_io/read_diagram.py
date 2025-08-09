from pathlib import Path

from networkx import DiGraph

from cemento.draw_io.constants import BadDiagramError, DiagramKey
from cemento.draw_io.io import write_error_diagram
from cemento.draw_io.preprocessing import (
    find_errors_diagram_content,
    get_diagram_error_exemptions,
)
from cemento.draw_io.transforms import (
    extract_elements,
    generate_graph,
    parse_elements,
    relabel_graph_nodes_with_node_attr,
)
from cemento.term_matching.transforms import get_prefixes, get_strat_predicates_str
from cemento.utils.io import (
    get_default_defaults_folder,
    get_default_prefixes_file,
    get_default_references_folder,
)


def read_drawio(
    input_path: str | Path,
    onto_ref_folder: str | Path = None,
    prefixes_file: str | Path = None,
    defaults_folder: str | Path = None,
    relabel_key: DiagramKey = DiagramKey.LABEL,
    check_errors: bool = False,
    inverted_rank_arrow: bool = False,
) -> DiGraph:
    prefixes_file = get_default_prefixes_file() if not prefixes_file else prefixes_file
    defaults_folder = (
        get_default_defaults_folder() if not defaults_folder else defaults_folder
    )
    onto_ref_folder = (
        get_default_references_folder() if not onto_ref_folder else onto_ref_folder
    )

    elements = parse_elements(input_path)
    term_ids, rel_ids = extract_elements(elements)
    strat_props = None
    prefixes, inv_prefixes = get_prefixes(prefixes_file, onto_ref_folder)
    strat_props = get_strat_predicates_str(
        onto_ref_folder, defaults_folder, inv_prefixes
    )

    error_exemptions = get_diagram_error_exemptions(elements)

    if check_errors:
        print("Checking for diagram errors...")
        errors = find_errors_diagram_content(
            elements,
            term_ids,
            rel_ids,
            serious_only=True,
            error_exemptions=error_exemptions,
        )
        if errors:
            checked_diagram_path = write_error_diagram(input_path, errors)
            print(
                "The inputted file came down with the following problems. Please fix them appropriately."
            )
            for elem_id, error in errors:
                print(elem_id, error)
            raise BadDiagramError(checked_diagram_path)

    print("generating graph...")
    graph = generate_graph(
        elements,
        term_ids,
        rel_ids,
        strat_terms=strat_props,
        exempted_elements=error_exemptions,
        inverted_rank_arrow=inverted_rank_arrow,
    )
    graph = relabel_graph_nodes_with_node_attr(graph, new_attr_label=relabel_key.value)
    return graph
