import re
from collections.abc import Iterable
from functools import partial
from os import scandir
from pathlib import Path

from cemento.draw_io.transforms import (
    clean_element_values,
    extract_elements,
    parse_elements,
)

diagram_test_files = [
    file.path
    for file in scandir(Path(__file__).parent / "test_files")
    if re.fullmatch(r"read-diagram-(\d+)", Path(file.path).stem)
]
diagram_test_files = sorted(diagram_test_files)


def assert_attrs(element: dict[str, dict[str, any]], keys: Iterable[str]) -> None:
    _, attrs = element
    for key in keys:
        assert key in attrs and attrs[key].strip()


def test_file_read():
    elements = parse_elements(diagram_test_files[0])
    elements = clean_element_values(elements)
    term_ids, rel_ids = extract_elements(elements)
    term_elements = list(filter(lambda x: x[0] in term_ids, elements.items()))
    rel_elements = list(filter(lambda x: x[0] in rel_ids, elements.items()))

    # test whether there are the correct number of terms and rels
    assert len(term_elements) == 5
    assert len(rel_elements) == 2

    # test if all term and rel elements have the required tags
    term_keys = ["parent", "value", "id"]
    rel_keys = ["source", "target", "parent", "id", "value"]
    map(partial(assert_attrs, keys=term_keys), term_elements)
    map(partial(assert_attrs, keys=rel_keys), rel_elements)

    # test whether the expected term values are present
    expected_terms = {"mds:one", "mds:three", "mds:four", "T-box", "A-box"}
    actual_terms = set(attr["value"] for _, attr in term_elements)
    assert actual_terms == expected_terms

    # test whether the expected term values are present
    expected_rels = {"mds:two", "mds:five"}
    actual_rels = set(attr["value"] for _, attr in rel_elements)
    assert actual_rels == expected_rels
