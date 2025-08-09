from collections import Counter
from pathlib import Path

from cemento.draw_io.constants import (
    BlankEdgeLabelError,
    BlankTermLabelError,
    DisconnectedTermError,
    FloatingEdgeError,
    MissingChildEdgeError,
    MissingParentEdgeError,
)
from cemento.draw_io.preprocessing import (
    find_errors_diagram_content,
    get_diagram_error_exemptions,
)
from cemento.draw_io.transforms import (
    extract_elements,
    parse_elements,
)

diagram_test_files = [
    Path(__file__).parent / "test_files" / f"diagram-error-{i:0>2}.drawio"
    for i in range(1, 6)
]


def get_diagram_errors(input_path: str | Path, with_exemptions=False):
    elements = parse_elements(input_path)
    term_ids, rel_ids = extract_elements(elements)
    error_exemptions = None
    if with_exemptions:
        error_exemptions = get_diagram_error_exemptions(elements)
    return find_errors_diagram_content(
        elements,
        term_ids,
        rel_ids,
        serious_only=True,
        error_exemptions=error_exemptions,
    )


def check_errors_by_count(
    errors: tuple[str, BaseException], expected_error_types: dict[BaseException, int]
):
    error_types = dict(Counter(type(error) for _, error in errors))
    total_error_ct = sum(error_types.values())
    expected_error_ct = sum(expected_error_types.values())
    print(error_types)
    assert total_error_ct == expected_error_ct
    assert error_types == expected_error_types


def test_exemptions():
    errors = get_diagram_errors(input_path=diagram_test_files[4])
    expected_error_types = {}
    check_errors_by_count(errors, expected_error_types)


def test_disconnection_errors():
    errors = get_diagram_errors(input_path=diagram_test_files[0])
    expected_error_types = {
        DisconnectedTermError: 6,
        MissingParentEdgeError: 1,
        MissingChildEdgeError: 1,
        FloatingEdgeError: 1,
    }
    check_errors_by_count(errors, expected_error_types)


def test_no_arrow_label_disconnection_errors():
    errors = get_diagram_errors(input_path=diagram_test_files[1])
    expected_error_types = {
        DisconnectedTermError: 6,
        BlankEdgeLabelError: 3,
        MissingParentEdgeError: 1,
        MissingChildEdgeError: 1,
        FloatingEdgeError: 1,
    }
    check_errors_by_count(errors, expected_error_types)


def test_no_term_labels_errors():
    errors = get_diagram_errors(input_path=diagram_test_files[2])
    expected_error_types = {BlankTermLabelError: 6, BlankEdgeLabelError: 1}
    check_errors_by_count(errors, expected_error_types)


def test_no_labels_disconnection_errors():
    errors = get_diagram_errors(input_path=diagram_test_files[3])
    expected_error_types = {
        DisconnectedTermError: 2,
        BlankTermLabelError: 2,
        BlankEdgeLabelError: 1,
        FloatingEdgeError: 1,
    }
    check_errors_by_count(errors, expected_error_types)
