import importlib.resources as pkg_resources
import os
from dataclasses import asdict
from pathlib import Path
from string import Template

import networkx as nx
from defusedxml import ElementTree as ET
from networkx import DiGraph
from thefuzz import process

from cemento.draw_io.constants import (
    FILL_COLOR,
    SHAPE_HEIGHT,
    SHAPE_WIDTH,
    Connector,
    DiagramInfo,
    DiagramKey,
    DiagramObject,
    GhostConnector,
    Shape,
)
from cemento.draw_io.preprocessing import clean_term


def parse_elements(file_path: str | Path) -> dict[str, dict[str, any]]:
    # parse elements
    tree = ET.parse(file_path)
    root = tree.getroot()
    root = next(tree.iter("root"))

    elements = dict()
    all_cells = [child for child in root.findall("mxCell")]  # only add base level cells

    for cell in all_cells:
        cell_attrs = dict()
        cell_attrs.update(cell.attrib)

        # add nested position attributes if any
        nested_attrs = dict()
        for subcell in cell.findall("mxGeometry"):
            nested_attrs.update(subcell.attrib)
        cell_attrs.update(nested_attrs)

        # add style attributes as data attributes
        if "style" in cell.attrib:
            style_terms = dict()
            style_tags = []
            for style_attrib_string in cell.attrib["style"].split(";"):
                style_term = style_attrib_string.split("=")
                if len(style_term) > 1:  # for styles with values
                    key, value = style_term
                    style_terms[key] = value
                elif style_term[0]:  # for style tags or names
                    style_tags.append(style_term[0])
            cell_attrs.update(style_terms)
            cell_attrs["tags"] = style_tags
            del cell_attrs["style"]  # remove style to prevent redundancy

        cell_id = cell.attrib["id"]
        del cell_attrs["id"]  # remove id since it is now used as a key
        elements[cell_id] = (
            cell_attrs  # set dictionary of cell key and attribute dictionary
        )

    return elements


def extract_elements(
    elements: dict[str, dict[str, any]],
) -> tuple[set[dict[str, any], set[str]]]:
    # read edges
    term_ids, rel_ids = set(), set()
    for element, data in elements.items():
        # if the vertex attribute is 1 and edgeLabel is not in tags, it is a term (shape)
        if (
            "vertex" in data
            and data["vertex"] == "1"
            and (
                "tags" not in data
                or ("tags" in data and "edgeLabel" not in data["tags"])
            )
        ):
            term_ids.add(element)
        # if an element has an edgeLabel tag, it is a relationship (connection)
        elif "tags" in data and "edgeLabel" in data["tags"]:
            rel_val = data["value"]
            rel_id = data["parent"]
            elements[rel_id]["value"] = rel_val
            rel_ids.add(rel_id)
        # if an element has value, source and target, it is also a relationship (connection)
        elif "value" in data and "source" in data and "target" in data:
            rel_val = data["value"]
            rel_id = element
            rel_ids.add(rel_id)
    return term_ids, rel_ids


def generate_graph(
    elements: dict[str, dict[str, any]],
    term_ids: set[str],
    relationship_ids: set[str],
    rank_terms: set[str],
    inverted_rank_arrow: bool = False,
) -> DiGraph:
    # for identified connectors, extract relationship information
    graph = nx.DiGraph()
    # add all terms
    for term_id in term_ids:
        term = elements[term_id]["value"]
        graph.add_node(term_id, term_id=term_id, label=clean_term(term))

    # add all relationships
    for rel_id in relationship_ids:
        subj_id = elements[rel_id]["source"]
        obj_id = elements[rel_id]["target"]
        pred = clean_term(elements[rel_id]["value"])

        matched_rank_pred, score = process.extractOne(
            pred.lower(), [rank_term.lower() for rank_term in rank_terms]
        )
        is_rank = score > 85
        pred = matched_rank_pred if is_rank else pred

        # arrow conventions are inverted for rank relationships, flip assignments to conform
        if inverted_rank_arrow and is_rank:
            temp = subj_id
            subj_id = obj_id
            obj_id = temp

        graph.add_edge(
            subj_id,
            obj_id,
            label=pred,
            pred_id=rel_id,
            is_rank=is_rank,
            is_predicate=True,
        )

    return graph


def relabel_graph_nodes(
    graph: DiGraph, new_attr_label=DiagramKey.TERM_ID.value
) -> DiGraph:
    node_info = nx.get_node_attributes(graph, new_attr_label)
    relabel_mapping = {
        current_node_label: node_info[current_node_label]
        for current_node_label in graph.nodes
    }
    return nx.relabel_nodes(graph, relabel_mapping)


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
    tree = tree.copy()
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
    tree = tree.copy()
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
    x_pos: float, y_pos: float, origin_x: float = 0, origin_y: float = 0
) -> tuple[int, int]:
    rect_width = 200
    rect_height = 80
    x_padding = 5
    y_padding = 20

    grid_x = rect_width * 2 + x_padding
    grid_y = rect_height * 2 + y_padding

    return ((x_pos + origin_x) * grid_x, (y_pos + origin_y) * grid_y)


def generate_shapes(
    graph: DiGraph,
    diagram_uid: str,
    offset_x: int = 0,
    offset_y: int = 0,
    idx_start: int = 0,
    shape_color: str = FILL_COLOR,
    shape_height: int = SHAPE_HEIGHT,
    shape_width: int = SHAPE_WIDTH,
) -> list[Shape]:
    nodes = [node for node in graph.nodes]
    entity_ids = (f"{diagram_uid}-{idx + idx_start}" for idx in range(len(nodes)))
    shape_pos_x = (graph.nodes[node]["draw_x"] + offset_x for node in nodes)
    shape_pos_y = (graph.nodes[node]["draw_y"] + offset_y for node in nodes)
    shape_positions = map(
        lambda x: translate_coords(x[0], x[1]),
        zip(shape_pos_x, shape_pos_y, strict=True),
    )
    node_contents = (node.replace('"', "&quot;") for node in nodes)
    shapes = [
        Shape(
            shape_id=entity_id,
            shape_content=node_content,
            fill_color=shape_color,
            x_pos=shape_pos_x,
            y_pos=shape_pos_y,
            shape_width=shape_width,
            shape_height=shape_height,
        )
        for (entity_id, node_content, (shape_pos_x, shape_pos_y)) in zip(
            entity_ids, node_contents, shape_positions, strict=True
        )
    ]
    return shapes


def get_template_files() -> dict[str, str | Path]:
    current_file_folder = Path(__file__)
    # retrieve the template folder from the grandparent directory
    template_path = current_file_folder.parent.parent.parent / "templates"

    if not template_path.exists():
        template_path = pkg_resources.files("cemento").joinpath("templates")

    template_files = [
        Path(file) for file in os.scandir(template_path) if file.name.endswith(".xml")
    ]
    template_dict = dict()
    for file in template_files:
        with open(file, "r") as f:
            template = Template(f.read())
            template_dict[file.stem] = template
    return template_dict


def generate_diagram_content(
    diagram_name: str, diagram_uid: str, *diagram_objects: list[DiagramObject]
) -> str:
    diagram_info = DiagramInfo(diagram_name, diagram_uid)

    diagram_content = ""
    templates = get_template_files()
    diagram_content += "".join(
        [
            templates[obj.template_key].substitute(asdict(obj))
            for objects in diagram_objects
            for obj in objects
        ]
    )
    diagram_info.diagram_content = diagram_content
    write_content = templates[diagram_info.template_key].substitute(
        asdict(diagram_info)
    )
    return write_content


def get_shape_ids(shapes: list[Shape]) -> dict[str, str]:
    return {shape.shape_content: shape.shape_id for shape in shapes}


def get_shape_positions(shapes: list[Shape]) -> dict[str, tuple[float, float]]:
    return {shape.shape_content: (shape.x_pos, shape.y_pos) for shape in shapes}


def get_rank_connectors(
    trees: list[DiGraph],
    shape_ids: dict[str, str],
    diagram_uid: str,
    entity_idx_start: int = 0,
):
    connectors = []
    connector_idx = entity_idx_start + 1
    for subtree in trees:
        new_connectors = []
        for subj, obj, data in subtree.edges(data=True):
            pred = data["label"].replace('"', "").strip()
            new_connectors.append(
                Connector(
                    connector_id=f"{diagram_uid}-{connector_idx}",
                    source_id=shape_ids[subj],
                    target_id=shape_ids[obj],
                    connector_label_id=f"{diagram_uid}-{connector_idx + 1}",
                    connector_val=pred,
                )
            )
            connector_idx += 2
        connectors.extend(new_connectors)
    return connectors


def get_predicate_connectors(
    graph: DiGraph,
    shape_positions: dict[str, tuple[float, float]],
    shape_ids: dict[str, str],
    diagram_uid: str,
    entity_idx_start: int = 0,
):
    predicate_connectors = []
    connector_idx = entity_idx_start + 1
    property_edges = (
        (subj, obj, data["label"])
        for subj, obj, data in graph.edges(data=True)
        if not data["is_rank"]
    )
    for subj, obj, pred in property_edges:
        new_connector = GhostConnector(
            connector_id=f"{diagram_uid}-{connector_idx}",
            source_id=shape_ids[subj],
            target_id=shape_ids[obj],
            connector_label_id=f"{diagram_uid}-{connector_idx + 1}",
            connector_val=pred,
        )
        predicate_connectors.append(new_connector)
        new_connector.resolve_position(
            "property", shape_positions[subj], shape_positions[obj]
        )
        connector_idx += 2
    return predicate_connectors
