import json
import re
from collections.abc import Iterable
from functools import partial
from os import scandir
from pathlib import Path
from pprint import pprint

from cemento.draw_io.read_diagram import read_drawio
from cemento.draw_io.transforms import (
    extract_elements,
    parse_elements,
)
from cemento.utils.utils import fst

diagram_test_files = [
    file.path
    for file in scandir(Path(__file__).parent / "test_files")
    if re.fullmatch(r"read-diagram-(\d+)", Path(file.path).stem)
]
diagram_test_files = sorted(diagram_test_files)

def get_corresponding_ref_file(input_file: str | Path):
    ref_folder_path = Path(__file__).parent / "test_refs"
    ref_path = f"{ref_folder_path / Path(diagram_test_files[1]).stem}.json"
    return ref_path

def assert_attrs(element: dict[str, dict[str, any]], keys: Iterable[str]) -> None:
    _, attrs = element
    for key in keys:
        assert key in attrs and attrs[key].strip()


def test_file_read():
    elements = parse_elements(diagram_test_files[0])
    term_ids, rel_ids = extract_elements(elements)
    term_elements = list(filter(lambda x: fst(x) in term_ids, elements.items()))
    rel_elements = list(filter(lambda x: fst(x) in rel_ids, elements.items()))

    # test whether there are the correct number of terms and rels
    assert len(term_elements) == 5
    assert len(rel_elements) == 2

    # test if all term and rel elements have the required tags
    term_keys = ["parent", "value", "id"]
    rel_keys = ["source", "target", "parent", "id", "value", "tags"]
    map(partial(assert_attrs, keys=term_keys), term_elements)
    map(partial(assert_attrs, keys=rel_keys), rel_elements)

    # test whether the expected term values are present
    print("actual term elements:")
    pprint(term_elements)
    print()
    expected_terms = {"mds:one", "mds:three", "mds:four", "T-box", "A-box"}
    actual_terms = set(attr["value"] for _, attr in term_elements)
    assert actual_terms == expected_terms

    # test whether the expected term values are present
    print("actual rel elements:")
    pprint(rel_elements)
    expected_rels = {"mds:two", "mds:five"}
    actual_rels = set(attr["value"] for _, attr in rel_elements)
    assert actual_rels == expected_rels


def remove_attr(input_dict: dict[str, any], remove_key: str) -> dict[str, any]:
    return {key: value for key, value in input_dict.items() if key != remove_key}


def get_graph_reference(
    input_path: str | Path,
) -> tuple[dict[str, dict[str, any]], list[list[any]]]:
    with open(input_path, "r") as f:
        ref_graph_data = json.load(f)
        return ref_graph_data["nodes"], ref_graph_data["edges"]
    raise ValueError("Cannot retrieve reference file!")


def test_graph_generation_basic():
    graph = read_drawio(diagram_test_files[1], check_errors=True)
    ref_path = get_corresponding_ref_file(diagram_test_files[1])
    ref_nodes, ref_edges = get_graph_reference(ref_path)
    graph_nodes, graph_edges = dict(graph.nodes(data=True)), list(
        graph.edges(data=True)
    )

    # check that the nodes and edges all have unique IDs
    node_ids = [attr["term_id"] for attr in graph_nodes.values()]
    assert len(node_ids) == len(set(node_ids))

    all_ids = node_ids
    edge_ids = [attr["pred_id"] for (_, _, attr) in graph_edges]
    assert len(edge_ids) == len(set(edge_ids))

    all_ids += edge_ids

    assert len(all_ids) == len(set(all_ids))

    # check that the parsed graph elements correspond with the reference
    # start with nodes
    ref_nodes = {key: remove_attr(attr, "term_id") for key, attr in ref_nodes.items()}
    graph_nodes = {
        key: remove_attr(value, "term_id") for key, value in graph_nodes.items()
    }

    assert graph_nodes == ref_nodes

    # then compare edges
    ref_edges = {
        (subj, obj, frozenset(remove_attr(attr, "pred_id").items()))
        for (subj, obj, attr) in ref_edges
    }
    graph_edges = {
        (subj, obj, frozenset(remove_attr(attr, "pred_id").items()))
        for (subj, obj, attr) in graph_edges
    }
    assert graph_edges == ref_edges