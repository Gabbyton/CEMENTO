from itertools import chain
from pathlib import Path
from uuid import uuid4

from networkx import DiGraph, selfloop_edges

from cemento.draw_io.constants import Connector, DiagramObject, Shape
from cemento.draw_io.preprocessing import (
    escape_shape_content,
    remove_literal_connector_id,
    remove_literal_shape_id,
    replace_term_quotes,
)
from cemento.draw_io.transforms import (
    compute_draw_positions,
    compute_grid_allocations,
    conform_instance_draw_positions,
    conform_tree_positions,
    flip_edges,
    flip_edges_of_graphs,
    generate_diagram_content,
    get_divider_line_annotations,
    get_non_ranked_strat_edges,
    get_predicate_connectors,
    get_rank_connectors_from_trees,
    get_rank_strat_connectors,
    get_ranked_subgraph,
    get_severed_link_connectors,
    get_shape_ids,
    get_shape_positions,
    get_shape_positions_by_id,
    get_shapes_from_trees,
    get_tree_dividing_line,
    get_tree_offsets,
    invert_tree,
    split_multiple_inheritances,
)
from cemento.utils.utils import get_graph_root_nodes, get_subgraphs


def draw_diagram(
    shapes: list[Shape],
    connectors: list[Connector],
    diagram_output_path: str | Path,
    *extra_elements: list[DiagramObject],
    diagram_uid: str = None,
) -> None:
    if diagram_uid is None:
        diagram_uid = str(uuid4()).split("-")[-1]

    shapes = list(map(escape_shape_content, shapes))
    shapes = map(remove_literal_shape_id, shapes)

    connectors = map(remove_literal_connector_id, connectors)

    write_content = generate_diagram_content(
        diagram_output_path.stem, diagram_uid, connectors, shapes, *extra_elements
    )

    with open(diagram_output_path, "w") as write_file:
        write_file.write(write_content)


def draw_tree(
    graph: DiGraph,
    diagram_output_path: str | Path,
    translate_x: int = 0,
    translate_y: int = 0,
    classes_only: bool = False,
    demarcate_boxes: bool = False,
    horizontal_tree: bool = False,
) -> None:
    diagram_output_path = Path(diagram_output_path)
    demarcate_boxes = demarcate_boxes and not classes_only
    # replace quotes to match shape content
    # TODO: prioritize is_rank terms over non-rank predicates when cutting
    graph = replace_term_quotes(graph)
    # remove graph cycles from the start
    graph.remove_edges_from(selfloop_edges(graph))
    ranked_graph = get_ranked_subgraph(graph)
    ranked_graph = ranked_graph.reverse(copy=True)

    not_rank_is_strat = get_non_ranked_strat_edges(ranked_graph)
    ranked_graph = flip_edges(
        ranked_graph, lambda subj, obj, data: (subj, obj) in not_rank_is_strat
    )
    ranked_subtrees = get_subgraphs(ranked_graph)
    split_subtrees, severed_links = zip(
        *map(split_multiple_inheritances, ranked_subtrees), strict=True
    )
    ranked_subtrees = [tree for trees in split_subtrees for tree in trees if tree]
    severed_links = [edge for edges in severed_links for edge in edges]

    ranked_subtrees = map(
        lambda subtree: compute_grid_allocations(
            subtree, get_graph_root_nodes(subtree)[0]
        ),
        ranked_subtrees,
    )

    ranked_subtrees = map(
        lambda subtree: compute_draw_positions(
            subtree, get_graph_root_nodes(subtree)[0]
        ),
        ranked_subtrees,
    )

    if demarcate_boxes:
        ranked_subtrees = map(conform_instance_draw_positions, ranked_subtrees)

    if horizontal_tree:
        ranked_subtrees = map(invert_tree, ranked_subtrees)

    try:
        ranked_subtrees = list(ranked_subtrees)
    except KeyError as e:
        offending_key = e.args[0]
        if demarcate_boxes:
            raise ValueError(
                f"The key {offending_key} is missing from the graph. Are you drawing a tree directly from a graph? Consider dropping -db if you are using the CLI. If you are using functions, think about setting demarcate_boxes to False."
            ) from KeyError
        raise ValueError(
            f"The input is lacking the key {offending_key} for an element. The graph may not have been processed completely."
        ) from KeyError
    # flip the rank terms after position calculation
    ranked_subtrees = flip_edges_of_graphs(
        ranked_subtrees,
        lambda subj, obj, data: data["is_rank"] if "is_rank" in data else False,
    )
    # flip the severed links after position computation
    severed_links = ((obj, subj, data) for subj, obj, data in severed_links)

    diagram_uid = str(uuid4()).split("-")[-1]
    entity_idx_start = 0

    tree_offsets = list(get_tree_offsets(ranked_subtrees))
    if horizontal_tree:
        tree_offsets = [(y, x) for x, y in tree_offsets]

    if demarcate_boxes:
        ranked_subtrees = conform_tree_positions(ranked_subtrees)

    shapes = get_shapes_from_trees(
        ranked_subtrees,
        diagram_uid,
        entity_idx_start=entity_idx_start,
        tree_offsets=tree_offsets,
    )

    entity_idx_start = len(shapes)
    new_shape_ids = get_shape_ids(shapes)
    shape_positions = get_shape_positions(shapes)

    rank_connectors = get_rank_connectors_from_trees(
        ranked_subtrees,
        shape_positions,
        new_shape_ids,
        diagram_uid,
        entity_idx_start=entity_idx_start + 1,
    )
    entity_idx_start += len(rank_connectors) * 2
    predicate_connectors = get_predicate_connectors(
        graph,
        shape_positions,
        new_shape_ids,
        diagram_uid,
        entity_idx_start=entity_idx_start + 1,
    )
    entity_idx_start += len(rank_connectors) * 2
    severed_link_connectors = get_severed_link_connectors(
        severed_links,
        shape_positions,
        new_shape_ids,
        diagram_uid,
        entity_idx_start=entity_idx_start + 1,
    )
    entity_idx_start += len(severed_link_connectors) * 2

    shape_positions_by_id = get_shape_positions_by_id(shapes)

    rank_strat_connectors = get_rank_strat_connectors(
        graph, rank_connectors, new_shape_ids
    )
    for connector in chain(
        rank_connectors, predicate_connectors, severed_link_connectors
    ):
        connector.resolve_position(
            shape_positions_by_id[connector.source_id],
            shape_positions_by_id[connector.target_id],
            strat_only=classes_only or connector in rank_strat_connectors,
            horizontal_tree=horizontal_tree,
        )
    all_connectors = rank_connectors + predicate_connectors + severed_link_connectors

    divider_lines, divider_annotations = [], []
    if demarcate_boxes:
        divider_lines = [
            get_tree_dividing_line(
                tree,
                f"{diagram_uid}-{entity_idx_start + idx + 1}",
                offset_x=offset_x,
                offset_y=offset_y,
            )
            for idx, (tree, (offset_x, offset_y)) in enumerate(
                zip(ranked_subtrees, tree_offsets, strict=False)
            )
        ]
        entity_idx_start += len(divider_lines)
        divider_idx_starts = map(
            lambda x: x + entity_idx_start + 1, range(0, len(divider_lines) * 2, 2)
        )
        divider_annotations = [
            get_divider_line_annotations(
                line, diagram_uid, label_id_start=label_id_start
            )
            for line, label_id_start in zip(
                divider_lines, divider_idx_starts, strict=True
            )
        ]
        divider_annotations = [ann for anns in divider_annotations for ann in anns]

    draw_diagram(
        shapes,
        all_connectors,
        diagram_output_path,
        divider_lines,
        divider_annotations,
        diagram_uid=diagram_uid,
    )
