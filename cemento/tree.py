import networkx as nx

from cemento.graph import Graph


class Tree(Graph):

    def __init__(
        self,
        file_path=None,
        rels_df=None,
        graph=None,
        ref=None,
        do_gen_ids=False,
        infer_rank=False,
        invert_tree=False,
        defer_layout=False,
    ):
        super().__init__(
            file_path=file_path,
            rels_df=rels_df,
            graph=graph,
            ref=ref,
            do_gen_ids=do_gen_ids,
            infer_rank=infer_rank,
        )
        self._root = None
        self._invert_tree = invert_tree
        self._defer_layout = defer_layout

    def get_subgraphs(self, input_tree=None):
        if not input_tree:
            input_tree = self.get_graph()

        subgraphs = [
            input_tree.subgraph(c).copy()
            for c in nx.weakly_connected_components(input_tree)
        ]

        subgraphs = [
            Tree(
                graph=subgraph,
                ref=self.get_ref(),
                invert_tree=self.get_invert_tree(),
                defer_layout=self.get_defer_layout(),
            )
            for subgraph in subgraphs
        ]
        return subgraphs

    def split_subgraph(self, subgraph):
        # create a dummy graph and connect root nodes to a dummy node
        dummy_graph = subgraph.copy()
        root_nodes = [
            node for node in dummy_graph.nodes if dummy_graph.in_degree(node) == 0
        ]

        dummy_graph.add_edges_from(("dummy", root_node) for root_node in root_nodes)
        fork_nodes = [
            node
            for node in nx.dfs_postorder_nodes(dummy_graph, source="dummy")
            if len(list(dummy_graph.predecessors(node))) > 1
        ]

        if len(fork_nodes) == 0:
            return [subgraph], []

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

        subtrees = [
            dummy_graph.subgraph(nodes).copy()
            for nodes in nx.weakly_connected_components(dummy_graph)
        ]

        return subtrees, severed_links

    def _compute_grid_allocs(self):
        for node in self.get_nodes():
            set_reserved_x = 1 if self._graph.out_degree(node) == 0 else 0
            self.set_attr(node, "reserved_x", set_reserved_x)
            self.set_attr(node, "reserved_y", 1)

        for node in reversed(list(nx.bfs_tree(self.get_graph(), self.get_root()))):
            if len(nx.descendants(self.get_graph(), node)) > 0:
                max_reserved_y = 0
                for child in self._graph.successors(node):
                    new_reserved_x = self.get_attr(node, "reserved_x") + self.get_attr(
                        child, "reserved_x"
                    )
                    max_reserved_y = max(
                        max_reserved_y, self.get_attr(child, "reserved_y")
                    )
                    self.set_attr(node, "reserved_x", new_reserved_x)

                new_reserved_y = max_reserved_y + self.get_attr(node, "reserved_y")
                self.set_attr(node, "reserved_y", new_reserved_y)

    def _compute_draw_pos(self):
        nodes_drawn = set()
        for level, nodes_in_level in enumerate(
            nx.bfs_layers(self.get_graph(), self.get_root())
        ):
            for node in nodes_in_level:
                # assign y-level to current level
                self.set_attr(node, "draw_y", level)
                nodes_drawn.add(node)

        # start cursor at a zero-origin
        self.set_attr(self.get_root(), "cursor_x", 0)
        # iterate over nodes in dfs to assign cursor positions
        for node in nx.dfs_preorder_nodes(self.get_graph(), self.get_root()):
            offset_x = 0  # re-initialize offset relative to sibling to zero
            cursor_x = self.get_attr(node, "cursor_x")  # get the current x-cursor

            # iterate over children to assign cursors with inherited parent cursor
            for child in self._graph.successors(node):
                child_cursor_x = (
                    cursor_x + offset_x
                )  # inherit parent cursor and add offset relative to already-drawn siblings
                self.set_attr(child, "cursor_x", child_cursor_x)
                offset_x += self.get_attr(child, "reserved_x")

            self.set_attr(
                node, "draw_x", (2 * cursor_x + self.get_attr(node, "reserved_x")) / 2
            )  # assign draw position at midpoint between x-span and cursor
            nodes_drawn.add(node)

        remaining_nodes = self.get_nodes() - nodes_drawn

        for node in remaining_nodes:
            reserved_x = self.get_attr(node, "reserved_x")
            try:
                cursor_x = self.get_attr(node, "cursor_x")
            except (KeyError, ValueError):
                cursor_x = 0
            self.set_attr(node, "draw_x", cursor_x + reserved_x)

            reserved_y = self.get_attr(node, "reserved_y")
            try:
                cursor_y = self.get_attr(node, "cursor_y")
            except (KeyError, ValueError):
                cursor_y = 0
            self.set_attr(node, "draw_y", cursor_y + reserved_y)

        if self.get_invert_tree():
            for node in self.get_nodes():
                draw_x = self.get_attr(node, "draw_x")
                draw_y = self.get_attr(node, "draw_y")

                self.set_attr(node, "draw_x", draw_y)
                self.set_attr(node, "draw_y", draw_x)

    def draw_tree(
        self, write_diagram, translate_x=0, translate_y=0, draw_predicates=True
    ):

        term_uids = dict()
        subgraph_sizes = dict()
        ranked_graph = self._create_graph(self.get_rank_edges())
        ranked_subtrees = self.get_subgraphs(input_tree=ranked_graph)
        all_ranked_subtrees = []
        all_severed_links = []

        for subtree in ranked_subtrees:
            extra_subgraphs, severed_links = self.split_subgraph(subtree.get_graph())
            all_ranked_subtrees.extend(
                [
                    Tree(
                        graph=subgraph,
                        ref=self.get_ref(),
                        invert_tree=self.get_invert_tree(),
                        defer_layout=self.get_defer_layout(),
                    )
                    for subgraph in extra_subgraphs
                ]
            )
            all_severed_links.extend(severed_links)

        for subtree in all_ranked_subtrees:
            # compute draw positions
            write_diagram.update_graph_count(1)
            current_tree_ct = write_diagram.get_graph_count()

            if self.get_defer_layout():
                for term_id in subtree.get_nodes():
                    subtree.set_attr(term_id, "draw_x", 0)
                    subtree.set_attr(term_id, "draw_y", 0)
                    subtree.set_attr(term_id, "reserved_x", 0)
                    subtree.set_attr(term_id, "reserved_y", 0)
            else:
                subtree._compute_grid_allocs()
                subtree._compute_draw_pos()

            # draw each node
            for term_id in subtree.get_nodes():
                term_content = subtree._ref.get_term(term_id)
                pos_x, pos_y = (
                    subtree.get_attr(term_id, "draw_x") + translate_x,
                    subtree.get_attr(term_id, "draw_y") + translate_y,
                )
                self.set_attr(term_id, "pos_x", pos_x)
                self.set_attr(term_id, "pos_y", pos_y)
                self.set_attr(term_id, "tree_number", current_tree_ct)
                term_uids[term_id] = write_diagram.add_shape(term_content, pos_x, pos_y)

            for edge in subtree.get_edges():
                parent_id, child_id = edge
                rel_content = subtree._ref.get_rel_from_edge(edge)
                write_diagram.add_connector(
                    term_uids[parent_id],
                    term_uids[child_id],
                    rel_content,
                    is_rank=True,
                    inverted=self.get_invert_tree(),
                )

            if self.get_defer_layout():
                subgraph_size = (0, 0)
            else:
                subgraph_size = subtree.get_size()
            subgraph_sizes[write_diagram.get_graph_count()] = subgraph_size
            if self.get_invert_tree():
                translate_x += subgraph_size[1]
            else:
                translate_x += subgraph_size[0]

        if draw_predicates:
            self._draw_predicates(term_uids, write_diagram, subgraph_sizes)

        for parent_id, child_id in all_severed_links:
            rel_content = self._ref.get_rel_from_edge((parent_id, child_id))

            write_diagram.add_connector(
                term_uids[parent_id],
                term_uids[child_id],
                rel_content,
                is_rank=True,
                inverted=self.get_invert_tree(),
            )

    def _draw_predicates(self, term_uids, write_diagram, subgraph_sizes):
        y_offset = dict()

        for edge in self.get_predicate_edges():
            parent_id, child_id, _ = edge
            drawn_ids = set(term_uids.keys())

            if parent_id not in drawn_ids and child_id not in drawn_ids:
                continue
            elif parent_id not in drawn_ids or child_id not in drawn_ids:
                created_id = parent_id if parent_id in drawn_ids else child_id
                uncreated_id = child_id if child_id not in drawn_ids else parent_id
                # add created_id to dictionary if not already there
                if created_id not in y_offset.keys():
                    y_offset[created_id] = 0
                # compute new term parameters
                uncreated_content = self._ref.get_term(uncreated_id)
                pos_x = self.get_attr(created_id, "pos_x")
                tree_end_y = subgraph_sizes[self.get_attr(created_id, "tree_number")][1]
                pos_y = tree_end_y + y_offset[created_id]
                # create new shape for term and add to ids
                self.add_node(uncreated_id)
                self.set_attr(uncreated_id, "pos_x", pos_x)
                self.set_attr(uncreated_id, "pos_y", pos_y)
                term_uids[uncreated_id] = write_diagram.add_shape(
                    uncreated_content, pos_x, pos_y
                )
                y_offset[created_id] += 0.5

            # create new connector
            edge = (parent_id, child_id) = edge[:2]  # only key with the id tuple
            rel_content = self._ref.get_rel_from_edge(edge)

            write_diagram.add_connector(
                term_uids[parent_id],
                term_uids[child_id],
                rel_content,
                is_rank=False,
                inverted=self.get_invert_tree(),
            )

    def get_invert_tree(self):
        return self._invert_tree

    def get_root(self):
        if not self._root:
            try:
                self._root = next(nx.topological_sort(self._graph))
            except Exception:
                self._root = None
                return self._root
        return self._root

    def get_size(self):
        root = self.get_root()

        if not self.get_attr(root, "reserved_x") or not self.get_attr(
            root, "reserved_y"
        ):
            self._compute_grid_allocs()

        return (self.get_attr(root, "reserved_x"), self.get_attr(root, "reserved_y"))

    def get_defer_layout(self):
        return self._defer_layout
