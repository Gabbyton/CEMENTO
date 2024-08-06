from os import path
import uuid
from datetime import datetime, timezone

from cemento.draw_io.diagram import Diagram
from cemento.draw_io.diagram_ref import DiagramRef

class Shape:

    def __init__(self, id, content, x_pos, y_pos, width, height, ref):
        self._id = id
        self._content = content
        self._x_pos = x_pos
        self._y_pos = y_pos
        self._width = width
        self._height = height
        self._ref = ref
        self._prefix = None
        self._template_key = 'shape'

        self._parse_prefix()

    def _parse_prefix(self):
        try:
            term_sep = self._ref.get_shape_param('term_separator')
            prefix, term_name = self._content.split(term_sep)
            self._prefix = prefix
        except ValueError:
            self._prefix = None
        except AttributeError:
            self._prefix = None

    def _get_fill_color(self):
        try:
            return self._ref.get_term_color(self.get_prefix())
        except KeyError:
            return self._ref.get_term_color('default')

    def get_prefix(self):
        return self._prefix

    def get_id(self):
        return self._id

    def get_content(self):
        return self._content

    def get_x_pos(self):
        return self._x_pos

    def get_y_pos(self):
        return self._y_pos

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height

    def get_ref(self):
        return self._ref

    def set_ref(self, ref):
        self._ref = ref

    def get_key(self):
        return self._template_key

    def get_props(self):
        return {
            'shape_id': self.get_id(),
            'shape_content': self.get_content(),
            'fill_color': self._get_fill_color(),
            'x_pos': self.get_x_pos(),
            'y_pos': self.get_y_pos(),
            'shape_width': self.get_width(),
            'shape_height': self.get_height()
        }

class Circle(Shape):

    def __init__(self, id, content, x_pos, y_pos, radius, ref):
        super().__init__(id, content, x_pos, y_pos, radius, radius, ref)
        self._radius = radius
        self._template_key = 'circle'

class Connector:

    def __init__(self, id, source_id, target_id, connector_label_id, connector_content, is_rank=None, start_x=None, start_y=None, end_x=None, end_y=None, inverted=False):
        self._id = id
        self._source_id = source_id
        self._target_id = target_id
        self._connector_label_id = connector_label_id
        self._connector_content = connector_content
        self._is_rank = is_rank
        self._start_pos_x = start_x
        self._start_pos_y = start_y
        self._end_pos_x = end_x
        self._end_pos_y = end_y
        self._inverted = inverted
        self._template_key = 'connector'

        if is_rank is None:
            self._is_rank = False

        self._is_dashed = 0 if self.get_is_rank() else 1
        self._is_curved = 0 if self.get_is_rank() else 1

        if not(start_x and start_y and end_x and end_y):
            self._update_start_end_pos()

    def _update_start_end_pos(self):
            if self.get_is_rank() and self.get_is_inverted():
                self._start_pos_x = 1
                self._end_pos_x = 0
                self._start_pos_y = 0.5
                self._end_pos_y = 0.5

            if not self.get_is_rank():
                self._start_pos_x = 0.5
                self._end_pos_x = 0.5
                self._start_pos_y = 0.5
                self._end_pos_y = 0.5

            if self.get_is_rank() and not self.get_is_inverted():
                self._start_pos_x = 0.5
                self._end_pos_x = 0.5
                self._start_pos_y = 1
                self._end_pos_y = 0

    def get_id(self):
        return self._id

    def get_source_id(self):
        return self._source_id

    def get_target_id(self):
        return self._target_id

    def get_connector_label_id(self):
        return self._connector_label_id

    def get_connector_content(self):
        return self._connector_content

    def get_is_inverted(self):
        return self._inverted

    def get_is_rank(self):
        if self._is_rank is None:
            raise ValueError("Cannot use rank inference features. Please set is_rank or resort to manual connector positions.")
        return self._is_rank

    def get_start_pos_x(self):
        if self._start_pos_x is None:
            raise ValueError("Cannot access start and end positions. Use the is_rank argument or resort to manual connector positions.")
        return self._start_pos_x

    def get_start_pos_y(self):
        return self._start_pos_y

    def get_end_pos_x(self):
        return self._end_pos_x

    def get_end_pos_y(self):
        return self._end_pos_y

    def get_key(self):
        return self._template_key

    def _get_is_dashed(self):
        return self._is_dashed

    def _get_is_curved(self):
        return self._is_curved

    def get_props(self):
        # if the connection is a rank edge, invert the arrow position according to convention
        source_id = self.get_source_id() if self.get_is_rank() else self.get_target_id()
        target_id = self.get_target_id() if self.get_is_rank() else self.get_source_id()

        return {
            'connector_id': self.get_id(),
            'start_pos_x': self.get_start_pos_x(),
            'start_pos_y': self.get_start_pos_y(),
            'end_pos_x': self.get_end_pos_x(),
            'end_pos_y': self.get_end_pos_y(),
            'source_id': source_id,
            'target_id': target_id,
            'rel_x_pos': 0,
            'rel_y_pos': 0,
            'connector_label_id': self.get_connector_label_id(),
            'connector_val': self.get_connector_content(),
            'is_dashed': self._get_is_dashed(),
            'is_curved': self._get_is_curved(),
        }

class StraightConnector(Connector):

    def __init__(self, id, source_id, target_id, connector_label_id, connector_content, start_x=None, start_y=None, end_x=None, end_y=None):
        super().__init__(id, source_id, target_id, connector_label_id, connector_content, is_rank=False, start_x=start_x, start_y=start_y, end_x=end_x, end_y=end_y, inverted=False)
        self._template_key = "straight_connector"

class WriteDiagram(Diagram):

    def __init__(self, file_path, name=None, diagram_ref=None, uid_start=1):
        super().__init__(file_path)
        self._diagram_ref = diagram_ref
        self._local_uid = uid_start
        self._name = name
        self._included_graph_ct = 0
        self._shapes = dict()
        self._connectors = dict()

        if not self.get_diagram_ref():
            self.set_diagram_ref(DiagramRef())

        if not self.get_name():
            self._parse_file_name()

        self._set_diagram_headers()

    def _set_diagram_headers(self):
        self._date_modified = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z"
        self._diagram_id = str(uuid.uuid4()).split('-')[-1]

        self.set_grid_dx(self._diagram_ref.get_diagram_defaults('grid_dx'))
        self.set_grid_dy(self._diagram_ref.get_diagram_defaults('grid_dy'))
        self.set_grid_size(self._diagram_ref.get_diagram_defaults('grid_size'))
        self.set_page_width(self._diagram_ref.get_diagram_defaults('page_width'))
        self.set_page_height(self._diagram_ref.get_diagram_defaults('page_height'))

    def _parse_file_name(self):
        self._name = path.basename(self.get_file_path()).replace(r'\..*', '')

    def _retrieve_uid(self):
        self._local_uid += 1
        return self._local_uid - 1

    def add_shape(self, term_content, pos_x, pos_y, apply_scale=True):
        shape_uid = f"{self.get_diagram_id()}-{self._retrieve_uid()}"
        if apply_scale:
            pos_x, pos_y = self._translate_coords(pos_x, pos_y)
        draw_pos_x, draw_pos_y = pos_x, pos_y
        shape_width = self._diagram_ref.get_shape_param('rect_width')
        shape_height = self._diagram_ref.get_shape_param('rect_height')
        new_shape = Shape(shape_uid, term_content, draw_pos_x, draw_pos_y, shape_width, shape_height, self.get_diagram_ref())
        self._shapes[shape_uid] = new_shape

        return shape_uid

    def add_circle(self, term_content, pos_x, pos_y, apply_scale=True):
        shape_uid = f"{self.get_diagram_id()}-{self._retrieve_uid()}"
        if apply_scale:
            pos_x, pos_y = self._translate_coords(pos_x, pos_y)
        draw_pos_x, draw_pos_y = pos_x, pos_y
        shape_radius = self._diagram_ref.get_shape_param('circle_radius')
        new_shape = Circle(shape_uid, term_content, draw_pos_x, draw_pos_y, shape_radius, self.get_diagram_ref())
        self._shapes[shape_uid] = new_shape

        return(shape_uid)

    def add_connector(self, parent_id, child_id, rel_content, is_rank, inverted=False):
        connector_uid = f"{self.get_diagram_id()}-{self._retrieve_uid()}"
        label_connector_uid = f"{self.get_diagram_id()}-{self._retrieve_uid()}"
        new_connector = Connector(connector_uid, parent_id, child_id, label_connector_uid, rel_content, is_rank, inverted=inverted)
        self._connectors[connector_uid] = new_connector

        return connector_uid

    def add_straight_connector(self, parent_id, child_id, rel_content, start_pos_x=None, start_pos_y=None, end_pos_x=None, end_pos_y=None):
        connector_uid = f"{self.get_diagram_id()}-{self._retrieve_uid()}"
        label_connector_uid = f"{self.get_diagram_id()}-{self._retrieve_uid()}"
        new_connector = StraightConnector(connector_uid, parent_id, child_id, label_connector_uid, rel_content, start_x=start_pos_x, start_y=start_pos_y, end_x=end_pos_x, end_y=end_pos_y)
        self._connectors[connector_uid] = new_connector

        return connector_uid

    def draw(self):
        diagram_content = ""

        for connector in self._connectors.values():
            diagram_content += self._diagram_ref.get_template(connector.get_key()).substitute(connector.get_props())

        for shape in self._shapes.values():
            diagram_content += self._diagram_ref.get_template(shape.get_key()).substitute(shape.get_props())

        with open(self.get_file_path(), 'w') as write_file:
            write_content = self._diagram_ref.get_template('scaffold').substitute(self.get_props(diagram_content))
            write_file.write(write_content)

    def get_graph_count(self):
        return self._included_graph_ct

    def update_graph_count(self, add):
        self._included_graph_ct += add

    def get_diagram_ref(self):
        return self._diagram_ref

    def set_diagram_ref(self, diagram_ref):
        self._diagram_ref = diagram_ref

    def get_rank_connectors(self):
        return [connector for connector in self._connectors if connector.get_is_rank()]

    def get_props(self, diagram_content):
        return {
            'modify_date': self.get_modify_date(),
            'diagram_name': self.get_name(),
            'diagram_id': self.get_diagram_id(),
            'grid_dx': self.get_grid_dx(),
            'grid_dy': self.get_grid_dy(),
            'grid_size': self.get_grid_size(),
            'page_width': self.get_page_width(),
            'page_height': self.get_page_height(),
            'diagram_content': diagram_content
        }

    def _translate_coords(self, x_pos, y_pos, origin_x=0, origin_y=0):
        rect_width = self._diagram_ref.get_shape_param('rect_width')
        rect_height = self._diagram_ref.get_shape_param('rect_height')
        x_padding = self._diagram_ref.get_shape_param('x_padding')
        y_padding = self._diagram_ref.get_shape_param('y_padding')

        grid_x =  rect_width * 2 + x_padding
        grid_y = rect_height * 2 + y_padding

        return ((x_pos + origin_x) * grid_x, (y_pos + origin_y) * grid_y)