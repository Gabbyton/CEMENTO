from pathlib import Path
import importlib.resources as pkg_resources
from configparser import ConfigParser

class GraphRef:

    def __init__(self, terms, rels, rels_id):
        self._terms = terms
        self._rels = rels
        self._rels_id = rels_id
        self._config = None

        self._read_config()

    def _read_config(self):
        config = ConfigParser()

        current_file_folder = Path(__file__)
        # retrieve configuration file from the grandparent directory
        config_path = current_file_folder.parent.parent /  "config.ini"

        if config_path.exists():
            config.read(config_path)
        else:
            with pkg_resources.open_text('cemento', 'config.ini') as config_file:
                config.read_file(config_file)

        self._config = config

    def get_term(self, id):
        return self._terms[id]
    
    def get_rel(self, id):
        return self._rels[id]
    
    def get_rel_from_edge(self, edge):
        return self._rels[self._rels_id[edge]]
    
    def get_rel_id(self, edge):
        try:
            return self._rels_id[edge]
        except KeyError:
            return None