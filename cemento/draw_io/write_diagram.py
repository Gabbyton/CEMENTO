from itertools import chain
from pathlib import Path
from uuid import uuid4

from networkx import DiGraph

from cemento.draw_io.preprocessing import (
    remove_literal_connector_id,
    remove_literal_shape_id,
    replace_shape_html_quotes,
    replace_term_quotes,
)
from cemento.draw_io.transforms import (
    compute_draw_positions,
    compute_grid_allocations,
    flip_edges,
    flip_edges_of_graphs,
    generate_diagram_content,
    get_graph_root_nodes,
    get_non_ranked_strat_edges,
    get_predicate_connectors,
    get_rank_connectors_from_trees,
    get_ranked_subgraph,
    get_severed_link_connectors,
    get_shape_ids,
    get_shape_positions,
    get_shape_positions_by_id,
    get_shapes_from_trees,
    get_subgraphs,
    split_multiple_inheritances,
)


def draw_tree(
    graph: DiGraph,
    diagram_output_path: str | Path,
    translate_x: int = 0,
    translate_y: int = 0,
    classes_only: bool = False,
    horizontal_tree: bool = False,
) -> None:
    diagram_output_path = Path(diagram_output_path)
    # replace quotes to match shape content
    # TODO: prioritize is_rank terms over non-rank predicates when cutting
    graph = replace_term_quotes(graph)
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
            subtree, get_graph_root_nodes(subtree)[0], horizontal_tree=horizontal_tree
        ),
        ranked_subtrees,
    )

    # flip the graph back once the positions have been computed
    graph = graph.reverse(copy=True)

    ranked_subtrees = list(ranked_subtrees)

    ranked_subtrees = flip_edges_of_graphs(
        ranked_subtrees, lambda subj, obj, data: (obj, subj) in not_rank_is_strat
    )

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
    entity_idx_start += len(connectors) * 2
    severed_link_connectors = get_severed_link_connectors(
        graph,
        severed_links,
        shape_positions,
        new_shape_ids,
        diagram_uid,
        entity_idx_start=entity_idx_start + 1,
    )

    shape_positions_by_id = get_shape_positions_by_id(shapes)

    for connector in chain(connectors, predicate_connectors, predicate_connectors):
        connector.resolve_position(
            shape_positions_by_id[connector.source_id],
            shape_positions_by_id[connector.target_id],
            classes_only=classes_only,
            horizontal_tree=horizontal_tree,
        )

    shapes = map(remove_literal_shape_id, shapes)
    connectors = map(remove_literal_connector_id, connectors)
    predicate_connectors = map(remove_literal_connector_id, predicate_connectors)
    severed_link_connectors = map(remove_literal_connector_id, severed_link_connectors)

    write_content = generate_diagram_content(
        diagram_output_path.stem,
        diagram_uid,
        connectors,
        predicate_connectors,
        severed_link_connectors,
        shapes,
    )

    with open(diagram_output_path, "w") as write_file:
        write_file.write(write_content)
