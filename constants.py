from dataclasses import dataclass

SHAPE_WIDTH = 200
SHAPE_HEIGHT  = 80
x_padding = 10
y_padding = 20

@dataclass
class Connector:
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
    id: str
    content: str
    x_pos: int
    y_pos: int
    width: int
    height: int
