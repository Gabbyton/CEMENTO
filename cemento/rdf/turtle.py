from collections import defaultdict

from rdflib.namespace import split_uri

from cemento.graph import Graph


class Turtle(Graph):

    def __init__(self, file_path, graph=None, prefixes=None):
        super().__init__(
            file_path=file_path,
            rels_df=None,
            graph=graph,
            ref=None,
            do_gen_ids=True,
            infer_rank=False,
        )
        self._file_path = file_path
        self._rdf_graph = None
        self._rename_vars = defaultdict(list)
        self._prefixes = None

    def get_rdf_graph(self):
        return self._rdf_graph

    def get_prefix(self, uri):
        return self._prefixes[uri]

    def _get_rename_vars(self):
        return self._rename_vars

    def get_abbrev_name(self, term):
        uri, abbrev_name = split_uri(term)
        prefix = self.get_prefix(uri)
        abbrev_name = f"{prefix}:{abbrev_name}"
        return abbrev_name

    def get_common_name(self, term):
        try:
            rename_vars = self._get_rename_vars()
            return rename_vars[term][0]
        except (IndexError, KeyError):
            return term

    def get_all_names(self, term):
        return self._rename_vars[term]
