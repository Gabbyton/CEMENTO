import networkx as nx
import pandas as pd

from cemento.draw_io.diagram_ref import DiagramRef
from cemento.graphref import GraphRef


class Graph:

    def __init__(
        self,
        file_path=None,
        rels_df=None,
        graph=None,
        ref=None,
        do_gen_ids=False,
        infer_rank=False,
    ):
        self._file_path = file_path
        self._rels_df = rels_df
        self._graph = graph
        self._ref = ref
        self._edges = None
        self._nodes = None
        self._predicate_edges = None
        self._rank_edges = None

        if (file_path is not None) + (graph is not None) + (rels_df is not None) != 1:
            raise TypeError(
                "Too many or too few arguments were provided. Either use file_path, graph or rels_df."
            )

        if file_path and rels_df is None:
            pass
        elif file_path or rels_df is not None:

            if file_path:
                terms, rels, rels_id, edges = self._read_edges(
                    do_gen_ids, infer_rank, file_path=self._file_path
                )
            elif rels_df is not None:
                terms, rels, rels_id, edges = self._read_edges(
                    do_gen_ids, infer_rank, rels_df=self._rels_df
                )

            self._ref = GraphRef(terms, rels, rels_id)

            self._predicate_edges = [edge for edge in edges if edge[2] == "predicate"]
            self._rank_edges = [edge for edge in edges if edge[2] == "rank"]
            unclassifed = [edge for edge in edges if edge[2] is None]

            self._edges = (
                self.get_predicate_edges() + self.get_rank_edges() + unclassifed
            )
            self._graph = self._create_graph(self._edges)

        if graph:
            self._edges = list(graph.edges())
            self._nodes = self._graph.nodes()

            if do_gen_ids:
                terms = {
                    term_id: term for term_id, term in enumerate(self._graph.nodes)
                }
                inv_terms = {term: term_id for term_id, term in terms.items()}
                # rels_id = {edge: rel_id for rel_id, edge in enumerate(self._graph.edges)}
                all_rels = {
                    edge_id: (
                        self._graph.get_edge_data(parent, child)["label"],
                        parent,
                        child,
                    )
                    for edge_id, (parent, child) in enumerate(self._graph.edges)
                }
                # assume rank for drawing
                # TODO: change to more sophisticated screening once graph conmplete
                rels_id = {
                    (inv_terms[parent], inv_terms[child]): edge_id
                    for edge_id, (_, parent, child) in all_rels.items()
                }
                rels = {edge_id: label for edge_id, (label, _, _) in all_rels.items()}

                edges = [(parent, child, "rank") for (parent, child) in rels_id.keys()]
                ref = GraphRef(terms, rels, rels_id)

                self._graph = nx.relabel_nodes(self._graph, inv_terms)
                self._edges = edges
                self._nodes = self._graph.nodes()

            if ref:
                self._ref = ref

    def _read_edges(self, do_gen_ids, infer_rank, file_path=None, rels_df=None):

        if file_path:
            df = pd.read_csv(file_path)

        if rels_df is not None:
            df = rels_df

        if not do_gen_ids and (
            "parent_id" not in df or "child_id" not in df or "rel_id" not in df
        ):
            raise AttributeError(
                "Not enough information in file. Consider using the gen_ids option or creating the parent_id, child_id or rel_id column in your file"
            )

        if do_gen_ids:
            unique_terms = list(df["parent"].unique()) + list(df["child"].unique())
            unique_term_set = set(unique_terms)
            term_id = {
                unique_term: idx for idx, unique_term in enumerate(unique_term_set)
            }

            df["parent_id"] = df["parent"].map(term_id)
            df["child_id"] = df["child"].map(term_id)
            df["comb_id_temp"] = (
                df["parent_id"].astype("string") + "_" + df["child_id"].astype("string")
            )
            df["rel_id"] = pd.factorize(df["comb_id_temp"])[0]

            df.drop("comb_id_temp", axis=1, inplace=True)

        if infer_rank:
            temp_diagram_ref = DiagramRef()
            df["is_rank"] = df["rel"].map(temp_diagram_ref.is_rank)

        terms = {term_id: term for term_id, term in zip(df["parent_id"], df["parent"])}
        terms.update(
            {term_id: term for term_id, term in zip(df["child_id"], df["child"])}
        )
        rels = {edge_id: edge for edge_id, edge in zip(df["rel_id"], df["rel"])}
        rels_id = {
            (parent_id, child_id): rel_id
            for parent_id, child_id, rel_id in zip(
                df["parent_id"], df["child_id"], df["rel_id"]
            )
        }

        if "is_rank" in df:
            edges = [
                (parent, child, "rank" if is_rank else "predicate")
                for parent, child, is_rank in zip(
                    df["parent_id"], df["child_id"], df["is_rank"]
                )
            ]
        else:
            edges = [
                (parent, child, None)
                for parent, child in zip(df["parent_id"], df["child_id"])
            ]

        return terms, rels, rels_id, edges

    def _create_graph(self, edges):
        graph = nx.DiGraph()

        for u, v, edge_type in edges:
            graph.add_edge(u, v, type=edge_type)

        return graph

    def set_ref(self, ref):
        self._ref = ref

    def get_rels_df(self):
        if self._rels_df is None:
            raise ValueError(
                "the relationship dataframe is not set. Please consider setting or reinitializing the object."
            )
        return self._rels_df

    def set_attr(self, node, attr, value):
        self._graph.nodes[node][attr] = value

    def get_graph(self):
        return self._graph

    def get_nodes(self):
        if self._nodes:
            return self._nodes
        return []

    def add_node(self, new_node_id):
        self._graph.add_node(new_node_id)

    def get_ref(self):
        return self._ref

    def get_edges(self):
        if self._edges:
            return self._edges
        return []

    def get_predicate_edges(self):
        if self._predicate_edges:
            return self._predicate_edges
        return []

    def get_rank_edges(self):
        if self._rank_edges:
            return self._rank_edges
        return []

    def get_attr(self, node, attr):
        return self._graph.nodes[node][attr]
