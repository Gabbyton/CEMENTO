from collections import defaultdict
import math
import networkx as nx
from cemento.graph import Graph

# TODO: move to graph ref
DEFAULT_LEVEL = 4

class CircleGraph(Graph):

    def __init__(
        self,
        file_path=None,
        rels_df=None,
        graph=None,
        ref=None,
        do_gen_ids=False,
        node_distance=20,
        scale=1000,
        center=(0, 0),
        iterations=1000,
        min_edge_weight = 10,
        max_edge_weight = 50
    ):
        super().__init__(
            file_path=file_path,
            rels_df=rels_df,
            graph=graph,
            ref=ref,
            do_gen_ids=do_gen_ids,
            infer_rank=False
        )
        self._node_distance = node_distance
        self._scale = scale
        self._center = center
        self._iterations = iterations
        self._min_edge_weight = min_edge_weight
        self._max_edge_weight = max_edge_weight

    def compute_draw_pos(self):
        # Compute the positions of nodjes using the spring_layout function
        node_level = defaultdict(lambda: DEFAULT_LEVEL)
        max_level = 0
        edges = [(u, v) for u, v, rel_type in self.get_edges() if rel_type == 'rank']
        temp_graph = nx.DiGraph(edges)
        temp_subgraphs = [temp_graph.subgraph(c).copy() for c in nx.weakly_connected_components(temp_graph)]
        for subgraph in temp_subgraphs:
            root = next(nx.topological_sort(subgraph))
            levels = nx.single_source_shortest_path_length(subgraph, root)
            for node, level in levels.items():
                node_level[node] = level
                max_level = max(max_level, level)

        input_graph = self._graph.to_undirected()

        for edge_pair in input_graph.edges():
            u, v = edge_pair
            edge_weight = (node_level[u] - node_level[v])

            min_weight = self.get_min_edge_weight()
            max_weight = self.get_max_edge_weight()

            edge_weight = (min_weight/math.sqrt(max_weight/min_weight)) * (math.sqrt(50/10)**edge_weight)
            nx.set_edge_attributes(input_graph, {(u, v): {'weight': edge_weight}})

        positions = nx.spring_layout(
            input_graph,
            k=self.get_node_distance(),
            scale=self.get_scale(),
            center=self.get_center(),
            iterations=self.get_iterations()
        )

        # Assign the x and y coordinates as attributes to each node
        for node, pos in positions.items():
            self.set_attr(node, "draw_x", pos[0])
            self.set_attr(node, "draw_y", pos[1])

        return positions

    def draw_graph(self, write_diagram, positions=None):
        term_uids = dict()

        if not positions:
            self.compute_draw_pos()

        for term_id in self.get_nodes():
            term_content = self._ref.get_term(term_id)
            pos_x, pos_y = self.get_attr(term_id, "draw_x"), self.get_attr(term_id, "draw_y")
            term_uids[term_id] = write_diagram.add_circle(term_content, pos_x, pos_y, apply_scale=False)

        for edge in self.get_edges():
            parent_id, child_id, _ = edge
            rel_content = self._ref.get_rel_from_edge((parent_id, child_id))

            parent_x, parent_y = self.get_attr(parent_id, 'draw_x'), self.get_attr(parent_id, 'draw_y')
            child_x, child_y = self.get_attr(child_id, 'draw_x'), self.get_attr(child_id, 'draw_y')
            angle = math.atan2((child_y - parent_y), (child_x - parent_x))
            start_x, start_y = CircleGraph.get_square_coordinate(angle)
            end_x, end_y = CircleGraph.get_square_coordinate(angle)

            write_diagram.add_straight_connector(
                term_uids[parent_id],
                term_uids[child_id],
                rel_content,
                start_pos_x=start_x,
                start_pos_y=start_y,
                end_pos_x=end_x,
                end_pos_y=end_y
            )

    def get_node_distance(self):
        return self._node_distance

    def set_node_distance(self, spring_constant):
        self._node_distance = spring_constant
        self.compute_draw_pos()

    def get_scale(self):
        return self._scale

    def set_scale(self, scale):
        self._scale = scale
        self.compute_draw_pos()

    def get_center(self):
        return self._center

    def set_center(self, center_x, center_y):
        self._center = (center_x, center_y)
        self.compute_draw_pos()

    def get_iterations(self):
        return self._iterations

    def set_iterations(self, iterations):
        self._iterations = iterations
        self.compute_draw_pos()

    def get_min_edge_weight(self):
        return self._min_edge_weight

    def get_max_edge_weight(self):
        return self._max_edge_weight

    @staticmethod
    def get_square_coordinate(angle, translate_x=0, translate_y=0):
        return ((math.cos(angle) + translate_x) * 0.5 + 0.5, (math.sin(angle) + translate_y) * 0.5 + 0.5)