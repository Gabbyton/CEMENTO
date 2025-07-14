from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DiagramKey(Enum):
    TERM_ID = "term_id"
    LABEL = "label"


SHAPE_WIDTH = 200
SHAPE_HEIGHT = 80
x_padding = 10
y_padding = 20


def get_timestamp_str():
    return f"{datetime.now():%Y-%m-%dT%H:%M:%S.%fZ}"


class DiagramObject:
    pass

@dataclass
class DiagramInfo(DiagramObject):
    diagram_name: int
    diagram_id: int
    modify_date: str = field(default_factory=get_timestamp_str)
    grid_dx: int = 1600
    grid_dy: int = 850
    grid_size: int = 10
    page_width: int = 1100
    page_height: int = 850
    diagram_content: int = None
    template_key: str = 'scaffold'


@dataclass
class Connector(DiagramObject):
    id: str
    source_id: str
    target_id: str
    connector_label_id: str
    connector_content: str
    is_rank: str
    start_x: str
    start_y: str
    end_x: str
    end_y: str


@dataclass
class Shape:
    shape_id: str
    shape_content: str
    fill_color: str
    x_pos: int
    y_pos: int
    shape_width: int
    shape_height: int
    template_key: str = 'shape'
