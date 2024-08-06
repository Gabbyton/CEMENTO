from os import path

class Diagram:

    def __init__(self, file_path):

        self._file_path = file_path
        self._name = None
        self._modify_date = None
        self._diagram_id = None
        self._grid_dx = None
        self._grid_dy = None
        self._grid_size = None
        self._page_width = None
        self._page_height = None

        self._name = self._set_name()

    def set_file_path(self, file_path):
        self._file_path = file_path
        self._set_name()

    def get_file_path(self):
        return self._file_path

    def _set_name(self):
        self._name = path.basename(self._file_path)

    def get_name(self):
        return self._name

    def get_modify_date(self):
        return self._modify_date

    def set_modify_date(self, modify_date):
        self._modify_date = modify_date

    def get_diagram_id(self):
        return self._diagram_id

    def get_grid_dx(self):
        return self._grid_dx

    def set_grid_dx(self, grid_dx):
        self._grid_dx = grid_dx

    def get_grid_dy(self):
        return self._grid_dy

    def set_grid_dy(self, grid_dy):
        self._grid_dy = grid_dy

    def get_grid_size(self):
        return self._grid_size

    def set_grid_size(self, grid_size):
        self._grid_size = grid_size

    def get_page_width(self):
        return self._page_width

    def set_page_width(self, page_width):
        self._page_width = page_width

    def get_page_height(self):
        return self._page_height

    def set_page_height(self, page_height):
        self._page_height = page_height