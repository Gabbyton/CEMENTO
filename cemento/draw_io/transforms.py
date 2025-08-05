from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import asdict
from functools import partial, reduce
from itertools import accumulate, starmap
from pathlib import Path

import networkx as nx
from defusedxml import ElementTree as ET
from networkx import DiGraph

from cemento.draw_io.constants import (
    FILL_COLOR,
    SHAPE_HEIGHT,
    SHAPE_WIDTH,
    STROKE_COLOR,
    ClassShape,
    Connector,
    DiagramInfo,
    DiagramKey,
    DiagramObject,
    InstanceShape,
    Label,
    Line,
    LiteralShape,
    NxEdge,
    NxStringEdge,
    Shape,
    ShapeType,
)
from cemento.draw_io.io import get_template_files
from cemento.draw_io.preprocessing import clean_term, remove_predicate_quotes
from cemento.term_matching.constants import RANK_PROPS
from cemento.term_matching.transforms import substitute_term
from cemento.utils.utils import aggregate_defaultdict, filter_graph, fst, snd, trd


def parse_elements(file_path: str | Path) -> dict[str, dict[str, any]]:
    # parse elements
    tree = ET.parse(file_path)

    elements = dict()
    all_cells = [
        child for root in tree.iter("root") for child in root.findall("mxCell")
    ]

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
    # remove root IDs that get added due to draw.io bugs
    reserved_root_ids = {"0", "1"}
    term_ids -= reserved_root_ids
    rel_ids -= reserved_root_ids
    return term_ids, rel_ids


def generate_graph(
    elements: dict[str, dict[str, any]],
    term_ids: set[str],
    relationship_ids: set[str],
    strat_terms: set[str] = None,
    exempted_elements: set[str] = None,
    inverted_rank_arrow: bool = False,
) -> DiGraph:
    # for identified connectors, extract relationship information
    graph = nx.DiGraph()
    # add all terms
    term_ids = filter(
        lambda element_id: exempted_elements is None
        or element_id not in exempted_elements,
        term_ids,
    )
    relationship_ids = filter(
        lambda element_id: exempted_elements is None
        or element_id not in exempted_elements,
        relationship_ids,
    )
    for term_id in term_ids:
        term = elements[term_id]["value"]
        # TODO: find more sophisticated method to detect literals, or mention method in the docs
        graph.add_node(
            term_id,
            term_id=term_id,
            label=clean_term(term),
            is_literal=('"' in term or "&quot;" in term),
            parent=(
                term_info["parent"]
                if "parent" in (term_info := elements[term_id])
                else None
            ),
        )

    # add all relationships
    for rel_id in relationship_ids:
        try:
            subj_id = elements[rel_id]["source"]
            obj_id = elements[rel_id]["target"]
        except KeyError as e:
            raise ValueError(
                f"cannot access {e.args[0]} from the attributes of a relationship in the elements dictionary. Please take a look at relationship with id {rel_id}"
            ) from KeyError

        pred = clean_term(elements[rel_id]["value"])

        if strat_terms:
            pred, is_strat = substitute_term(pred, strat_terms)
        else:
            # default to just taking rank terms, which are always known
            is_strat = pred in RANK_PROPS
        # TODO: add set to a list on constants, dynamically retrieve
        pred, is_rank = substitute_term(pred, {"rdfs:subClassOf", "rdf:type"})
        # arrow conventions are inverted for rank relationships, flip assignments to conform
        if inverted_rank_arrow and is_strat:
            temp = subj_id
            subj_id = obj_id
            obj_id = temp

        graph.add_edge(
            subj_id,
            obj_id,
            label=pred,
            pred_id=rel_id,
            is_strat=is_strat,
            is_rank=is_rank,
            is_predicate=True,
        )

    return graph


def add_node_to_digraph(graph: DiGraph, node: tuple[any, dict[str, any]]) -> DiGraph:
    new_graph = graph.copy()
    new_graph.add_node(node)
    return new_graph


# TODO: add property definition to allow parsing container predicates as annotation types
def parse_containers(
    graph: DiGraph,
    strat_terms: set[str] = None,
    pred_symbol: str = "->",
    root_id: str = "1",
) -> DiGraph:
    new_graph = graph.copy()
    containers = (
        data["parent"]
        for term, data in graph.nodes(data=True)
        if "parent" in data and data["parent"] is not None
    )
    containers = set(filter(lambda x: x != root_id, containers))
    term_ids = {
        value: key for key, value in nx.get_node_attributes(graph, "term_id").items()
    }
    container_terms = [term_ids[container_id] for container_id in containers]

    container_child_pairs = (
        (container_id, term)
        for term, data in graph.nodes(data=True)
        if "parent" in data
        and (container_id := data["parent"]) is not None
        and container_id in containers
    )
    container_children = reduce(
        aggregate_defaultdict, container_child_pairs, defaultdict(list)
    )
    pred_terms, obj_terms = zip(
        *map(partial(str.split, sep=pred_symbol), container_terms), strict=True
    )
    sub_strat_pred_terms, is_strats = list(
        zip(
            *map(
                partial(substitute_term, search_terms=strat_terms, score_cutoff=95),
                pred_terms,
            ),
            strict=True,
        )
    )
    pred_terms = (
        substitute_term
        for substitute_term, _ in zip(sub_strat_pred_terms, pred_terms, strict=True)
    )
    pred_terms = list(pred_terms)
    sub_rank_pred_terms, is_ranks = list(
        zip(
            *map(
                partial(substitute_term, search_terms={"rdfs:subClassOf", "rdf:type"}),
                pred_terms,
            ),
            strict=True,
        )
    )
    pred_terms = (
        substitute_term
        for substitute_term, _ in zip(sub_rank_pred_terms, pred_terms, strict=True)
    )
    new_edge_data = {
        container_id: {
            "label": pred_term,
            "pred_id": f"{container_id}-1",
            "is_strat": is_strat,
            "is_rank": is_rank,
            "is_predicate": True,
        }
        for container_id, pred_term, is_strat, is_rank in zip(
            containers,
            pred_terms,
            is_strats,
            is_ranks,
            strict=True,
        )
    }
    obj_terms = list(obj_terms)
    new_edge_objects = {
        container_id: obj_term
        for container_id, obj_term in zip(containers, obj_terms, strict=True)
    }
    obj_term_data = (
        {
            "term_id": f"{container_id}-2",
            "label": clean_term(obj_term),
            "is_literal": ('"' in obj_term or "&quot;" in obj_term),
            "parent": container_id,
        }
        for container_id, obj_term in zip(containers, obj_terms, strict=True)
    )
    obj_term_nodes = (
        (obj_term, obj_term_data)
        for obj_term, obj_term_data in zip(obj_terms, obj_term_data, strict=True)
    )
    new_graph.add_nodes_from(obj_term_nodes)

    new_graph_triples = (
        (child, new_edge_objects[container_id], new_edge_data[container_id])
        for container_id, children in container_children.items()
        for child in children
    )
    new_graph.add_edges_from(new_graph_triples)
    new_graph.remove_nodes_from(container_terms)
    return new_graph


def relabel_graph_nodes_with_node_attr(
    graph: DiGraph, new_attr_label: str = DiagramKey.TERM_ID.value
) -> DiGraph:
    node_info = nx.get_node_attributes(graph, new_attr_label)
    relabel_mapping = {
        current_node_label: node_info[current_node_label]
        for current_node_label in graph.nodes
    }
    return nx.relabel_nodes(graph, relabel_mapping)


def get_non_ranked_strat_edges(graph: DiGraph) -> Iterable[tuple[any, any]]:
    return {
        (subj, obj)
        for subj, obj, data in graph.edges(data=True)
        if not data["is_rank"] and data["is_strat"]
    }


def flip_edges(
    graph: DiGraph, filter_func: Callable[[any, any, dict[str, any]], bool] = None
) -> DiGraph:
    to_remove = []
    new_graph = graph.copy()
    to_remove = [
        (subj, obj, data)
        for subj, obj, data in graph.edges(data=True)
        if (filter_func(subj, obj, data) if filter_func else True)
    ]
    new_graph.remove_edges_from(to_remove)
    new_graph.add_edges_from((obj, subj, data) for subj, obj, data in to_remove)
    return new_graph


def flip_edges_of_graphs(
    graphs: Iterable[DiGraph],
    filter_func: Callable[[any, any, dict[str, any]], bool] = None,
) -> Iterable[DiGraph]:
    return list(map(partial(flip_edges, filter_func=filter_func), graphs))


def get_ranked_subgraph(graph: DiGraph) -> DiGraph:
    return filter_graph(graph, lambda data: data["is_strat"])


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
            (predecessor, fork_node, dummy_graph.get_edge_data(predecessor, fork_node))
            for predecessor in fork_predecessors[1:]
        ]
        dummy_graph.remove_edges_from(edges_to_cut)
        severed_links.extend(edges_to_cut)

    for diamond_head in diamond_heads:
        diamond_successors = list(dummy_graph.successors(diamond_head))
        edges_to_cut = [
            (
                diamond_head,
                successor,
                dummy_graph.get_edge_data(diamond_head, successor),
            )
            for successor in diamond_successors[1:]
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


def get_tree_canvas_size(tree: DiGraph) -> tuple[float, float]:
    tree_canvas_size_x = max(nx.get_node_attributes(tree, "draw_x").values())
    tree_canvas_size_y = max(nx.get_node_attributes(tree, "draw_y").values())
    return (tree_canvas_size_x, tree_canvas_size_y)


def get_tree_extents(tree: DiGraph) -> tuple[tuple[float, float], tuple[float, float]]:
    min_tree_x = min(nx.get_node_attributes(tree, "draw_x").values())
    max_tree_x = max(nx.get_node_attributes(tree, "draw_x").values())
    min_tree_y = min(nx.get_node_attributes(tree, "draw_y").values())
    max_tree_y = max(nx.get_node_attributes(tree, "draw_y").values())
    return ((min_tree_x, max_tree_x), (min_tree_y, max_tree_y))


def get_divider_line_annotations(
    line: Line, diagram_uid: str, label_id_start: str
) -> list[Label]:
    annotation_x = line.start_pos_x
    # TODO: move to constants
    abox_annotation_y = line.start_pos_y
    tbox_annotation_y = line.start_pos_y - 40
    tbox_annotation = Label(
        shape_id=f"{diagram_uid}-{label_id_start}",
        shape_content="T-Box",
        x_pos=annotation_x,
        y_pos=tbox_annotation_y,
    )
    abox_annotation = Label(
        shape_id=f"{diagram_uid}-{label_id_start + 1}",
        shape_content="A-Box",
        x_pos=annotation_x,
        y_pos=abox_annotation_y,
    )
    return [tbox_annotation, abox_annotation]


def get_tree_dividing_line(
    tree: DiGraph,
    line_id: str,
    offset_x: float = 0,
    offset_y: float = 0,
    line_offset_y: float = 0.5,
) -> Line:
    line_start_x, line_end_x = fst(get_tree_extents(tree))
    line_start_x, line_end_x = line_start_x + offset_x, line_end_x + offset_x + 1
    _, tree_size_y = get_tree_canvas_size(tree)
    line_y = tree_size_y - line_offset_y + offset_y
    line_start_x, _ = translate_coords(line_start_x, 0)
    line_end_x, line_y = translate_coords(line_end_x, line_y)
    return Line(
        line_id=line_id,
        start_pos_x=line_start_x,
        start_pos_y=line_y,
        end_pos_x=line_end_x,
        end_pos_y=line_y,
    )


def shift_tree(tree: DiGraph, shift_x: float = 0, shift_y: float = 0) -> DiGraph:
    new_tree = tree.copy()
    if not all(["draw_y" in data for _, data in tree.nodes(data=True)]):
        raise ValueError(
            "The input tree has missing draw_y values. If this is a mistake, please make sure to compute draw positions before conforming."
        )
    updated_node_positions = {
        node: {"draw_x": data["draw_x"] + shift_x, "draw_y": data["draw_y"] + shift_y}
        for node, data in tree.nodes(data=True)
    }
    nx.set_node_attributes(new_tree, updated_node_positions)
    return new_tree


def conform_tree_positions(trees: list[DiGraph]) -> list[DiGraph]:
    max_y = snd(max(map(get_tree_canvas_size, trees), key=lambda size: snd(size)))
    tree_diffs = (max_y - snd(get_tree_canvas_size(tree)) for tree in trees)
    new_trees = [
        shift_tree(new_tree, shift_y=shift_y)
        for new_tree, shift_y in zip(trees, tree_diffs, strict=True)
    ]
    return new_trees


def conform_instance_draw_positions(tree: DiGraph, box_offset=1.5) -> DiGraph:
    if not all(["draw_y" in data for _, data in tree.nodes(data=True)]):
        raise ValueError(
            "The input tree has missing draw_y values. If this is a mistake, please make sure to compute draw positions before conforming."
        )
    new_tree = tree.copy()
    max_draw_x, max_draw_y = get_tree_canvas_size(new_tree)
    max_draw_y += box_offset

    instance_nodes = (
        node for node, data in new_tree.nodes(data=True) if data["is_instance"]
    )
    updated_instance_node_positions = {
        node: {"draw_y": max_draw_y} for node in instance_nodes
    }
    nx.set_node_attributes(new_tree, updated_instance_node_positions)
    return new_tree


def invert_tree(tree: DiGraph) -> DiGraph:
    new_tree = tree.copy()
    for node in new_tree.nodes:
        draw_x = new_tree.nodes[node]["draw_x"]
        draw_y = new_tree.nodes[node]["draw_y"]

        new_tree.nodes[node]["draw_y"] = draw_x
        new_tree.nodes[node]["draw_x"] = draw_y

    return new_tree


def compute_draw_positions(
    tree: DiGraph,
    root_node: any,
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

    return tree


def translate_coords(
    x_pos: float, y_pos: float, origin_x: float = 0, origin_y: float = 0
) -> tuple[int, int]:
    # TODO: retrieve shape constants from config
    rect_width = 200
    rect_height = 80
    scale_factor_x = 1.5
    scale_factor_y = 1.5
    x_padding = 5
    y_padding = 20

    grid_x = rect_width * scale_factor_x + x_padding
    grid_y = rect_height * scale_factor_y + y_padding

    return ((x_pos + origin_x) * grid_x, (y_pos + origin_y) * grid_y)


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


def get_shape_positions_by_id(shapes: list[Shape]) -> dict[str, tuple[float, float]]:
    return {shape.shape_id: (shape.x_pos, shape.y_pos) for shape in shapes}


def get_graph_edges(
    graph: DiGraph,
    data_filter: Callable[[dict[str, any]], bool] = None,
) -> Iterable[NxEdge]:
    return (
        NxEdge(subj=subj, obj=obj, pred=data["label"])
        for subj, obj, data in graph.edges(data=True)
        if (data_filter(data) if data_filter else True)
    )


def get_connectors(
    edges: list[NxStringEdge | tuple[str, str, str]],
    shape_positions: dict[str, tuple[float, float]],
    shape_ids: dict[str, str],
    diagram_uid: str,
    entity_idx_start: int = 0,
    connector_type: type[Connector] = Connector,
) -> list[Connector]:
    connector_ids = (
        f"{diagram_uid}-{idx + entity_idx_start}" for idx in range(0, len(edges) * 2, 2)
    )
    connector_label_ids = (
        f"{diagram_uid}-{idx + entity_idx_start + 1}"
        for idx in range(0, len(edges) * 2, 2)
    )
    connectors = [
        connector_type(
            connector_id=connector_id,
            source_id=shape_ids[subj],
            target_id=shape_ids[obj],
            connector_label_id=connector_label_id,
            connector_val=pred,
        )
        for (connector_id, connector_label_id, (subj, obj, pred)) in zip(
            connector_ids, connector_label_ids, edges, strict=True
        )
    ]
    return connectors


def get_rank_connectors(
    graph: DiGraph,
    shape_positions: dict[str, tuple[float, float]],
    shape_ids: dict[str, str],
    diagram_uid: str,
    entity_idx_start: int = 0,
) -> list[Connector]:
    rank_edges = map(
        lambda edge: NxEdge(subj=edge.subj, obj=edge.obj, pred=edge.pred),
        get_graph_edges(graph, data_filter=lambda data: data["is_strat"]),
    )
    rank_edges = remove_predicate_quotes(rank_edges)
    rank_edges = list(rank_edges)
    return get_connectors(
        rank_edges,
        shape_positions,
        shape_ids,
        diagram_uid,
        entity_idx_start,
        connector_type=Connector,
    )


def get_severed_link_connectors(
    edges: list[tuple[any, any, dict[str, any]]],
    shape_positions: dict[str, tuple[float, float]],
    shape_ids: dict[str, str],
    diagram_uid: str,
    entity_idx_start: int = 0,
):
    # TODO: remove all side effects, make it clear that the order is reversed!
    severed_edges = map(
        lambda edge: NxEdge(
            subj=fst(edge),
            obj=snd(edge),
            pred=trd(edge)["label"],
        ),
        edges,
    )
    severed_edges = remove_predicate_quotes(severed_edges)
    severed_edges = list(severed_edges)
    return get_connectors(
        severed_edges,
        shape_positions,
        shape_ids,
        diagram_uid,
        entity_idx_start,
        connector_type=Connector,
    )


def get_predicate_connectors(
    graph: DiGraph,
    shape_positions: dict[str, tuple[float, float]],
    shape_ids: dict[str, str],
    diagram_uid: str,
    entity_idx_start: int = 0,
) -> list[Connector]:
    property_edges = map(
        lambda edge: NxEdge(subj=edge.subj, obj=edge.obj, pred=edge.pred),
        get_graph_edges(graph, data_filter=lambda data: not data["is_strat"]),
    )
    property_edges = remove_predicate_quotes(property_edges)
    property_edges = list(property_edges)
    return get_connectors(
        property_edges,
        shape_positions,
        shape_ids,
        diagram_uid,
        entity_idx_start,
        connector_type=Connector,
    )


def get_rank_connectors_from_trees(
    trees: list[DiGraph],
    shape_positions: dict[str, tuple[float, float]],
    shape_ids: dict[str, str],
    diagram_uid: str,
    entity_idx_start: int = 0,
) -> list[Connector]:
    connector_idcs = accumulate(
        trees,
        lambda idx, graph: idx
        + len(list(get_graph_edges(graph, lambda data: data["is_strat"]))) * 2,
        initial=entity_idx_start,
    )
    rank_connectors_list = map(
        lambda tree_info: get_rank_connectors(
            fst(tree_info),
            shape_positions,
            shape_ids,
            diagram_uid,
            entity_idx_start=snd(tree_info),
        ),
        zip(trees, connector_idcs, strict=False),
    )
    return [
        connector for connectors in rank_connectors_list for connector in connectors
    ]


def get_rank_strat_connectors(
    graph: DiGraph, connectors: list[Connector], shape_id: dict[str, str]
) -> list[Connector]:
    rank_strat_set = set(
        (nx_edge.subj, nx_edge.obj)
        for nx_edge in get_graph_edges(
            graph, lambda data: data["is_strat"] and data["is_rank"]
        )
    )
    inv_shape_id = {value: key for key, value in shape_id.items()}
    rank_strat_connectors = [
        connector
        for connector in connectors
        if (inv_shape_id[connector.source_id], inv_shape_id[connector.target_id])
        in rank_strat_set
    ]
    return rank_strat_connectors


def get_shape_designation(node: any, node_attr: dict[str, any]) -> ShapeType:
    shape_type = ShapeType.UKNOWN
    if "is_class" in node_attr and node_attr["is_class"]:
        shape_type = ShapeType.CLASS
    elif "is_instance" in node_attr and node_attr["is_instance"]:
        shape_type = ShapeType.INSTANCE
    if "is_literal" in node_attr and node_attr["is_literal"]:
        shape_type = ShapeType.LITERAL
    return shape_type


def generate_shapes(
    graph: DiGraph,
    diagram_uid: str,
    offset_x: int = 0,
    offset_y: int = 0,
    idx_start: int = 0,
    shape_color: str = FILL_COLOR,
    stroke_color: str = STROKE_COLOR,
    shape_height: int = SHAPE_HEIGHT,
    shape_width: int = SHAPE_WIDTH,
) -> list[Shape]:
    nodes = [(node, data) for node, data in graph.nodes(data=True)]
    entity_ids = (f"{diagram_uid}-{idx + idx_start}" for idx in range(len(nodes)))
    shape_pos_x = (data["draw_x"] + offset_x for node, data in nodes)
    shape_pos_y = (data["draw_y"] + offset_y for node, data in nodes)
    shape_positions = map(
        lambda x: translate_coords(x[0], x[1]),
        zip(shape_pos_x, shape_pos_y, strict=True),
    )
    node_contents = (node for node, data in nodes)
    shape_templates = {
        ShapeType.CLASS: ClassShape,
        ShapeType.INSTANCE: InstanceShape,
        ShapeType.LITERAL: LiteralShape,
        ShapeType.UKNOWN: Shape,
    }
    node_shape_designations = starmap(get_shape_designation, nodes)
    shape_template_designations = map(
        lambda x: shape_templates[x], node_shape_designations
    )

    shapes = [
        ShapeTemplate(
            shape_id=entity_id,
            shape_content=node_content,
            fill_color=shape_color,
            stroke_color=stroke_color,
            x_pos=shape_pos_x,
            y_pos=shape_pos_y,
            shape_width=shape_width,
            shape_height=shape_height,
        )
        for (entity_id, node_content, (shape_pos_x, shape_pos_y), ShapeTemplate) in zip(
            entity_ids,
            node_contents,
            shape_positions,
            shape_template_designations,
            strict=True,
        )
    ]
    return shapes


def get_tree_offsets(
    trees: list[DiGraph],
    horizontal_tree: bool = False,
) -> Iterable[tuple[float, float]]:
    tree_sizes = map(get_tree_size, trees)
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
    return offsets


def get_shapes_from_trees(
    trees: list[DiGraph],
    diagram_uid: str,
    entity_idx_start: int = 0,
    tree_offsets: list[tuple[float, float]] = None,
    horizontal_tree: bool = False,
) -> list[Shape]:
    if tree_offsets is None:
        tree_offsets = get_tree_offsets(trees, horizontal_tree=horizontal_tree)

    entity_index_starts = accumulate(
        trees,
        lambda acc, tree: acc + len(tree.nodes),
        initial=entity_idx_start,
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
            trees, tree_offsets, entity_index_starts, strict=False
        )
    ]
    return [shape for shapes in shapes_list for shape in shapes]
