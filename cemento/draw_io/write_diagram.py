from collections import defaultdict
from itertools import chain
from pathlib import Path
from pprint import pprint
from uuid import uuid4

import networkx as nx
from networkx import DiGraph, selfloop_edges

from cemento.draw_io.constants import (
    DiagramContainer,
    DiagramContainerItem,
    DiagramPage,
)
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
    generate_diagram_file_content,
    generate_page,
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


def draw_tree_diagram(
    graph: DiGraph,
    diagram_output_path: str | Path,
    translate_x: int = 0,
    translate_y: int = 0,
    classes_only: bool = False,
    demarcate_boxes: bool = False,
    horizontal_tree: bool = False,
) -> None:
    diagram_output_path = Path(diagram_output_path)
    tree_page = draw_tree_page(
        graph,
        translate_x=translate_x,
        translate_y=translate_y,
        classes_only=classes_only,
        demarcate_boxes=demarcate_boxes,
        horizontal_tree=horizontal_tree,
    )
    axiom_page = draw_axiom_page(graph)
    diagram_file_content = generate_diagram_file_content(tree_page, axiom_page)
    with open(diagram_output_path, "w") as write_file:
        write_file.write(diagram_file_content)


def draw_axiom_page(graph: DiGraph) -> DiagramPage:
    axiom_graph = graph.subgraph(
        [node for node, attr in graph.nodes(data=True) if attr.get("is_axiom", False)]
    ).copy()
    collection_graph = graph.subgraph(
        [
            node
            for subj, obj, data in graph.edges(data=True)
            if data.get("is_collection", False)
            for node in (subj, obj)
        ]
    ).copy()

    # parse collection types and use to filter for containers of interest
    collection_types = {
        obj: subj
        for subj, obj, data in collection_graph.edges(data=True)
        if data.get("label", "") == "mds:CollectionType"
    }
    # parse the collections and build objects
    collection_member_triples = (
        (subj, obj)
        for subj, obj, data in collection_graph.edges(data=True)
        if subj in collection_types
        and data.get("label", "") == "mds:hasCollectionMember"
    )
    collection_members = defaultdict(list)
    for head, member in collection_member_triples:
        collection_members[head].append(member)
    valid_collection_terms = set(collection_members.keys())
    valid_collection_terms |= {
        value for values in collection_members.values() for value in values
    }
    parse_collection_subgraph = collection_graph.subgraph(valid_collection_terms).copy()
    containers = list(
        filter(
            lambda x: x in collection_members.keys(),
            nx.dfs_postorder_nodes(parse_collection_subgraph),
        )
    )
    graph_uuid = str(uuid4()).split("-")[-1]
    container_elements = dict()
    container_diagram_ids = dict()
    container_members = []
    container_parents = dict()
    container_element_idx = 2
    for container_id in containers:
        container_diagram_id = f"{graph_uuid}-{container_element_idx}"
        container_diagram_ids[container_id] = container_diagram_id
        container_element_idx += 1
        for member in collection_members[container_id]:
            if member in containers:
                container_parents[container_diagram_ids[member]] = (
                    container_diagram_ids[container_id]
                )
            else:
                container_members.append(
                    DiagramContainerItem(
                        f"{graph_uuid}-{container_element_idx}",
                        container_diagram_ids[container_id],
                        container_value=member,
                    )
                )
                container_element_idx += 1
        container_elements[container_diagram_id] = DiagramContainer(
            container_diagram_id,
            container_label_value=collection_types[container_id],
        )

    for container_diagram_id, parent_diagram_id in container_parents.items():
        container_elements[container_diagram_id].container_parent_id = parent_diagram_id

    # pprint(container_elements)
    # pprint(container_members)
    # get the root nodes that correspond to the core of each subtree
    # print(get_graph_root_nodes(axiom_graph))

    # create layouts for each subtree, ensuring that terms are duplicated

    return generate_page(
        "axioms", graph_uuid, container_elements.values(), container_members
    )


def draw_tree_page(
    graph: DiGraph,
    translate_x: int = 0,
    translate_y: int = 0,
    classes_only: bool = False,
    demarcate_boxes: bool = False,
    horizontal_tree: bool = False,
) -> DiagramPage:
    demarcate_boxes = demarcate_boxes and not classes_only
    # replace quotes to match shape content
    # TODO: prioritize is_rank terms over non-rank predicates when cutting
    # remove axiom_elements
    graph = graph.subgraph(
        [
            node
            for node, attr in graph.nodes(data=True)
            if attr.get("is_in_diagram", False)
        ]
    ).copy()
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

    shapes = list(map(escape_shape_content, shapes))
    shapes = map(remove_literal_shape_id, shapes)
    all_connectors = map(remove_literal_connector_id, all_connectors)

    return generate_page(
        "tree page",
        diagram_uid,
        shapes,
        all_connectors,
        divider_lines,
        divider_annotations,
    )
