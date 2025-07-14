from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from string import Template
from uuid import uuid4

import networkx as nx
from networkx import DiGraph

from constants import Shape

INPUT_PATH = "/Users/gabbython/dev/sdle/CEMENTO/sandbox/SyncXrayResult_graph.drawio"


def get_ranked_subgraph(graph: DiGraph) -> DiGraph:
    ranked_subgraph = graph.copy()
    ranked_subgraph.remove_edges_from(
        [
            (subj, obj)
            for subj, obj, data in graph.edges(data=True)
            if not data["is_rank"]
        ]
    )
    return ranked_subgraph


def get_subgraphs(graph: DiGraph) -> list[DiGraph]:
    subgraphs = nx.weakly_connected_components(graph)
    return [graph.subgraph(subgraph_nodes).copy() for subgraph_nodes in subgraphs]


def get_graph_root_nodes(graph: DiGraph) -> list[any]:
    return [node for node in graph.nodes if graph.in_degree(node) == 0]


def split_multiple_inheritances(
    graph: DiGraph,
) -> tuple[list[DiGraph], list[tuple[any, any]]]:
    # create a dummy graph and connect root nodes to a dummy node
    dummy_graph = graph.copy()
    root_nodes = get_graph_root_nodes(dummy_graph)
    dummy_graph.add_edges_from(("dummy", root_node) for root_node in root_nodes)
    fork_nodes = [
        node
        for node in nx.dfs_postorder_nodes(dummy_graph, source="dummy")
        if len(list(dummy_graph.predecessors(node))) > 1
    ]

    if len(fork_nodes) == 0:
        return [graph], []

    fork_levels = {
        node: nx.shortest_path_length(dummy_graph, source="dummy", target=node)
        for node in fork_nodes
    }
    sorted(fork_nodes, key=lambda x: fork_levels[x])
    dummy_graph.remove_node("dummy")

    diamond_heads = set()
    for root in root_nodes:
        for fork in fork_nodes:
            paths = list(nx.all_simple_paths(dummy_graph, source=root, target=fork))
            if len(paths) > 1:
                diamond_heads.add(paths[0][0])

    severed_links = list()
    for fork_node in fork_nodes:
        fork_predecessors = list(dummy_graph.predecessors(fork_node))
        edges_to_cut = [
            (predecessor, fork_node) for predecessor in fork_predecessors[1:]
        ]
        dummy_graph.remove_edges_from(edges_to_cut)
        severed_links.extend(edges_to_cut)

    for diamond_head in diamond_heads:
        diamond_successors = list(dummy_graph.successors(diamond_head))
        edges_to_cut = [
            (diamond_head, successor) for successor in diamond_successors[1:]
        ]
        dummy_graph.remove_edges_from(edges_to_cut)
        severed_links.extend(edges_to_cut)

    subtrees = get_subgraphs(dummy_graph)
    return subtrees, severed_links


def compute_grid_allocations(tree: DiGraph, root_node: any) -> DiGraph:
    for node in tree.nodes:
        set_reserved_x = 1 if tree.out_degree(node) == 0 else 0
        tree.nodes[node]["reserved_x"] = set_reserved_x
        tree.nodes[node]["reserved_y"] = 1

    for node in reversed(list(nx.bfs_tree(tree, root_node))):
        if len(nx.descendants(tree, node)) > 0:
            max_reserved_y = 0
            for child in tree.successors(node):
                new_reserved_x = (
                    tree.nodes[node]["reserved_x"] + tree.nodes[child]["reserved_x"]
                )
                max_reserved_y = max(max_reserved_y, tree.nodes[node]["reserved_y"])
                tree.nodes[node]["reserved_x"] = new_reserved_x
            new_reserved_y = max_reserved_y + tree.nodes[node]["reserved_y"]
            tree.nodes[node]["reserved_y"] = new_reserved_y
    return tree


def get_tree_size(tree: DiGraph) -> tuple[int, int]:
    tree_size_x = max(nx.get_node_attributes(tree, "reserved_x").values())
    tree_size_y = max(nx.get_node_attributes(tree, "reserved_y").values())
    return (tree_size_x, tree_size_y)


def compute_draw_positions(
    tree: DiGraph, root_node: any, horizontal_tree: bool = False
) -> DiGraph:
    nodes_drawn = set()
    for level, nodes_in_level in enumerate(nx.bfs_layers(tree, root_node)):
        for node in nodes_in_level:
            tree.nodes[node]["draw_y"] = level
            nodes_drawn.add(node)

    tree.nodes[root_node]["cursor_x"] = 0
    for node in nx.dfs_preorder_nodes(tree, root_node):
        offset_x = 0
        cursor_x = tree.nodes[node]["cursor_x"]

        for child in tree.successors(node):
            child_cursor_x = cursor_x + offset_x
            tree.nodes[child]["cursor_x"] = child_cursor_x
            offset_x += tree.nodes[child]["reserved_x"]

        tree.nodes[node]["draw_x"] = (2 * cursor_x + tree.nodes[node]["reserved_x"]) / 2
        nodes_drawn.add(node)

    remaining_nodes = tree.nodes - nodes_drawn
    for node in remaining_nodes:
        reserved_x = tree.nodes[node]["reserved_x"]
        reserved_y = tree.nodes[node]["reserved_y"]
        cursor_x = tree.nodes[node]["cursor_x"] if "cursor_x" in tree.nodes[node] else 0
        cursor_y = tree.nodes[node]["cursor_y"] if "cursor_y" in tree.nodes[node] else 0

        tree.nodes[node]["draw_x"] = cursor_x + reserved_x
        tree.nodes[node]["draw_y"] = cursor_y + reserved_y

    if horizontal_tree:
        for node in tree.nodes:
            draw_x = tree.nodes[node]["draw_x"]
            draw_y = tree.nodes[node]["draw_y"]

            tree.nodes[node]["draw_y"] = draw_x
            tree.nodes[node]["draw_x"] = draw_y

    return tree


def translate_coords(
    x_pos: int, y_pos: int, origin_x: int = 0, origin_y: int = 0
) -> tuple[int, int]:
    rect_width = 200
    rect_height = 80
    x_padding = 10
    y_padding = 20

    grid_x = rect_width * 2 + x_padding
    grid_y = rect_height * 2 + y_padding

    return ((x_pos + origin_x) * grid_x, (y_pos + origin_y) * grid_y)


def generate_shapes(subtree: DiGraph, diagram_uid: str, offset_x: int = 0, offset_y: int = 0, idx_start: int = 0) -> list[Shape]:
    shapes = []
    for idx, node in enumerate(subtree.nodes):
        entity_id = f"{diagram_uid}-{idx + idx_start}"
        shape_pos_x = subtree.nodes[node]["draw_x"] + offset_x
        shape_pos_y = subtree.nodes[node]["draw_y"] + offset_y
        shape_pos_x, shape_pos_y = translate_coords(shape_pos_x, shape_pos_y)
        shapes.append(
            Shape(
                entity_id,
                node,
                "#f2f3f4",
                shape_pos_x,
                shape_pos_y,
                200,
                80,
            )
        )
    return shapes


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
    split_result = map(split_multiple_inheritances, ranked_subtrees)
    split_subtrees, severed_links = zip(*split_result)
    ranked_subtrees = [tree for trees in split_subtrees for tree in trees]
    severed_links = [edge for edges in severed_links for edge in edges]

    diagram_uid = str(uuid4())
    # draw each of the trees
    offset_x, offset_y = 0, 0
    shapes = []
    for subtree in ranked_subtrees:
        roots = get_graph_root_nodes(subtree)
        root_node = roots[0]
        graph = compute_grid_allocations(subtree, root_node)
        graph = compute_draw_positions(subtree, root_node)
        tree_size_x, tree_size_y = get_tree_size(subtree)
        offset_x += tree_size_x
        offset_y += tree_size_y

    default_diagram_info = {
        "modify_date": f"{datetime.now():%Y-%m-%dT%H:%M:%S.%fZ}",
        "diagram_name": diagram_output_path.stem,
        "diagram_id": diagram_uid,
        "grid_dx": 1600,
        "grid_dy": 850,
        "grid_size": 10,
        "page_width": 1100,
        "page_height": 850,
        "diagram_content": None,
    }
    diagram_content = ""

    scaffold_path = "/Users/gabriel/dev/sdle/CEMENTO/cemento/templates/scaffold.xml"
    shape_path = "/Users/gabriel/dev/sdle/CEMENTO/cemento/templates/shape.xml"

    scaffold_template = Template(open(scaffold_path).read())
    shape_template = Template(open(shape_path).read())

    for shape in shapes:
        diagram_content += shape_template.substitute(asdict(shape))

    default_diagram_info["diagram_content"] = diagram_content
    print(diagram_content)

    with open(diagram_output_path, "w") as write_file:
        write_content = scaffold_template.substitute(default_diagram_info)
        write_file.write(write_content)
