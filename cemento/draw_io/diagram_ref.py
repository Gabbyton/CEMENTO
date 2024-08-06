import os
import importlib.resources as pkg_resources
from pathlib import Path
from configparser import ConfigParser
from string import Template

class DiagramRef:

    def __init__(self):
        self._templates = None
        self._term_colors = None
        self._diagram_defaults = None
        self._rank_list = None
        self._connector_list = None
        self._shape_params = None
        self._term_parser_titles = None
        self._term_parser_sep = None
        self._config = None

        self._read_config()
        self._read_templates()
        self._read_color_dict()
        self._read_defaults()
        self._read_rank_list()
        self._read_instance_connector_list()
        self._read_shape_params()
        self._read_term_parser_titles()
        self._read_term_parser_sep()

    def _read_config(self):
        config = ConfigParser()

        current_file_folder = Path(__file__)
        # retrieve configuration file from the grandparent directory
        config_path = current_file_folder.parent.parent.parent /  "config.ini"

        if config_path.exists():
            config.read(config_path)
        else:
            with pkg_resources.open_text('cemento', 'config.ini') as config_file:
                config.read_file(config_file)

        self._config = config

    def _read_templates(self):
        current_file_folder = Path(__file__)
        # retrieve the template folder from the grandparent directory
        template_path = current_file_folder.parent.parent.parent / "templates"

        if not template_path.exists():
            template_path = pkg_resources.files('cemento').joinpath('templates')

        template_files = [file for file in os.scandir(template_path) if file.name.endswith('.xml')]
        templates = {file.name.replace('.xml', ''): Template(open(file.path).read()) for file in template_files}
        self._templates = templates

    def _read_color_dict(self):
        config = self._get_config()
        color_dict = dict(config.items('term_colors'))
        self._term_colors = color_dict

    def _read_defaults(self):
        config = self._get_config()
        diagram_defaults = dict(config.items('diagram_defaults'))
        diagram_defaults = {key: int(value) for key, value in diagram_defaults.items()}
        self._diagram_defaults = diagram_defaults

    def _read_rank_list(self):
        config = self._get_config()
        sep = config['rank_terms']['sep']
        rank_list = config['rank_terms']['term_list'].split(sep)
        self._rank_list = [rank_term.lower() for rank_term in rank_list]

    def _read_instance_connector_list(self):
        config = self._get_config()
        sep = config['rank_terms']['sep']
        connector_list = config['rank_terms']['instance_connectors'].split(sep)
        self._connector_list = [rank_term.lower() for rank_term in connector_list]

    def _read_term_parser_titles(self):
        config = self._get_config()
        term_titles = dict(config.items('term_parser'))
        term_titles = {key.strip(): value.strip() for key, value in term_titles.items() if 'title' in key}
        self._term_parser_titles = term_titles

    def _read_term_parser_sep(self):
        config = self._get_config()
        term_sep = config['term_parser']['sep']
        self._term_parser_sep = term_sep

    def _read_shape_params(self):
        config = self._get_config()
        shape_param_dict = dict(config.items('shape_params'))
        shape_param_dict = {key: int(value) if value.isdigit() else value for key, value in shape_param_dict.items()}

        self._shape_params = shape_param_dict

    def _get_config(self):
        return self._config

    def get_term_color(self, term):
        if not self._term_colors:
            self._read_color_dict()

        if term not in self._term_colors:
            term = 'default'

        return self._term_colors[term]

    def get_template(self, key):
        if not self._templates:
            self._read_templates()
        return self._templates[key]

    def get_diagram_defaults(self, key):
        if not self._diagram_defaults:
            self._read_defaults()
        return self._diagram_defaults[key]

    def get_term_parser_title(self, key):
        if not self._term_parser_titles:
            self._read_term_parser_titles()
        return self._term_parser_titles[key]

    def get_term_parser_sep(self):
        return self._term_parser_sep

    def get_term_parser_titles(self):
        return self._term_parser_titles

    def is_rank(self, term):
        return term.lower() in self._rank_list

    def is_instance_connector(self, term):
        return term.lower() in self._connector_list

    def get_shape_param(self, key):
        if not self._shape_params:
            self._read_shape_params()
        return self._shape_params[key]