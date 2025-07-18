from pathlib import Path
from uuid import uuid4

from networkx import DiGraph

from cemento.draw_io.preprocessing import replace_shape_html_quotes, replace_term_quotes
from cemento.draw_io.transforms import (
    compute_draw_positions,
    compute_grid_allocations,
    generate_diagram_content,
    get_graph_root_nodes,
    get_predicate_connectors,
    get_rank_connectors_from_trees,
    get_ranked_subgraph,
    get_shape_ids,
    get_shape_positions,
    get_shapes_from_trees,
    get_subgraphs,
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
    # replace quotes to match shape content
    # TODO: prioritize is_rank terms over non-rank predicates when cutting
    graph = replace_term_quotes(graph)
    ranked_graph = get_ranked_subgraph(graph)
    ranked_graph = ranked_graph.reverse(copy=True)
    ranked_subtrees = get_subgraphs(ranked_graph)
    split_subtrees, severed_links = zip(
        *map(split_multiple_inheritances, ranked_subtrees), strict=True
    )
    ranked_subtrees = [tree for trees in split_subtrees for tree in trees]
    severed_links = [edge for edges in severed_links for edge in edges]
    print(severed_links)

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

    ranked_subtrees = list(ranked_subtrees)

    diagram_uid = str(uuid4()).split("-")[-1]
    entity_idx_start = 0

    shapes = get_shapes_from_trees(
        ranked_subtrees, diagram_uid, entity_idx_start, horizontal_tree=horizontal_tree
    )
    shapes = list(map(replace_shape_html_quotes, shapes))
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
    entity_idx_start += len(connectors) * 2
    predicate_connectors = get_predicate_connectors(
        graph,
        shape_positions,
        new_shape_ids,
        diagram_uid,
        entity_idx_start=entity_idx_start + 1,
    )

    write_content = generate_diagram_content(
        diagram_output_path.stem, diagram_uid, connectors, predicate_connectors, shapes
    )

    with open(diagram_output_path, "w") as write_file:
        write_file.write(write_content)
