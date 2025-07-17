from itertools import accumulate
from pathlib import Path
from uuid import uuid4

from networkx import DiGraph

from cemento.draw_io.preprocessing import fst, snd
from cemento.draw_io.transforms import (
    compute_draw_positions,
    compute_grid_allocations,
    generate_diagram_content,
    generate_shapes,
    get_graph_root_nodes,
    get_predicate_connectors,
    get_rank_connectors_from_trees,
    get_ranked_subgraph,
    get_shape_ids,
    get_shape_positions,
    get_subgraphs,
    get_tree_size,
    split_multiple_inheritances,
)


def draw_tree(
    graph: DiGraph,
    diagram_output_path: str | Path,
    translate_x: int = 0,
    translate_y: int = 0,
    horizontal_tree: bool = False,
) -> None:
    diagram_output_path = Path(diagram_output_path)
    ranked_graph = get_ranked_subgraph(graph)
    ranked_graph = ranked_graph.reverse(copy=True)
    ranked_subtrees = get_subgraphs(ranked_graph)
    split_subtrees, severed_links = zip(
        *map(split_multiple_inheritances, ranked_subtrees), strict=True
    )
    ranked_subtrees = [tree for trees in split_subtrees for tree in trees]
    severed_links = [edge for edges in severed_links for edge in edges]

    shapes = []
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

    diagram_uid = str(uuid4()).split("-")[-1]
    entity_idx_start = 0
    ranked_subtrees = list(ranked_subtrees)
    tree_sizes = map(get_tree_size, ranked_subtrees)
    entity_index_starts = accumulate(
        ranked_subtrees,
        lambda acc, tree: acc + len(tree.nodes),
        initial=entity_idx_start,
    )
    offsets = accumulate(
        tree_sizes,
        lambda acc, x: (fst(acc) + fst(x), snd(acc) + snd(x)),
        initial=(0, 0),
    )
    offsets = map(
        lambda x: (
            fst(x) if not horizontal_tree else 0,
            snd(x) if horizontal_tree else 0,
        ),
        offsets,
    )
    shapes_list = [
        generate_shapes(
            subtree,
            diagram_uid,
            offset_x=offset_x,
            offset_y=offset_y,
            idx_start=entity_idx_start,
        )
        for (subtree, (offset_x, offset_y), entity_idx_start) in zip(
            ranked_subtrees, offsets, entity_index_starts, strict=False
        )
    ]
    shapes = [shape for shapes in shapes_list for shape in shapes]

    entity_idx_start = len(shapes)
    new_shape_ids = get_shape_ids(shapes)
    shape_positions = get_shape_positions(shapes)
    connectors = get_rank_connectors_from_trees(
        ranked_subtrees,
        shape_positions,
        new_shape_ids,
        diagram_uid,
        entity_idx_start=entity_idx_start + 1,
    )
    predicate_connectors = get_predicate_connectors(
        graph,
        shape_positions,
        new_shape_ids,
        diagram_uid,
        entity_idx_start=entity_idx_start + len(connectors) * 2 + 1,
    )
    write_content = generate_diagram_content(
        diagram_output_path.stem, diagram_uid, connectors, predicate_connectors, shapes
    )
    with open(diagram_output_path, "w") as write_file:
        write_file.write(write_content)
