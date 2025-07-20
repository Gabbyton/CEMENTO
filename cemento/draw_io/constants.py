from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from math import atan2, pi
from typing import NamedTuple


class DiagramKey(Enum):
    TERM_ID = "term_id"
    LABEL = "label"


SHAPE_WIDTH = 200
SHAPE_HEIGHT = 80
FILL_COLOR = "#f2f3f4"
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
    template_key: str = "scaffold"


class ConnectorType(Enum):
    RANK_CONNECTOR = "rank"
    PROPERTY_CONNECTOR = "property"


@dataclass
class Connector(DiagramObject):
    connector_id: str
    source_id: str
    target_id: str
    connector_label_id: str
    connector_val: str
    rel_x_pos: float = 0
    rel_y_pos: float = 0
    start_pos_x: float = 0.5
    start_pos_y: float = 1
    end_pos_x: float = 0.5
    end_pos_y: float = 0
    is_dashed: bool = 0
    is_curved: bool = 0
    template_key: str = "connector"

    @staticmethod
    def compute_dynamic_position(
        source_shape_x: float,
        source_shape_y: float,
        target_shape_x: float,
        target_shape_y: float,
    ) -> tuple[float, float, float, float]:
        crit_angle = abs(atan2(SHAPE_HEIGHT, SHAPE_WIDTH))
        angle = atan2(target_shape_y - source_shape_y, target_shape_x - source_shape_x)

        if -crit_angle <= angle <= crit_angle:
            return (1, 0.5, 0, 0.5)
        elif crit_angle < angle <= pi - crit_angle:
            return (0.5, 1, 0.5, 0)
        elif angle > pi - crit_angle or angle < -(pi - crit_angle):
            return (0, 0.5, 1, 0.5)
            # return (1, 0.5, 0, 0.5)
        elif -(pi - crit_angle) <= angle < -crit_angle:
            return (0.5, 0, 0.5, 1)
        else:
            return (0, 0, 0, 0)

    def resolve_position(
        self,
        source_shape_pos: tuple[float, float],
        target_shape_pos: tuple[float, float],
        classes_only: bool = False,
        horizontal_tree: bool = False,
    ) -> None:

        if not classes_only:
            self.start_pos_x, self.start_pos_y, self.end_pos_x, self.end_pos_y = (
                Connector.compute_dynamic_position(*source_shape_pos, *target_shape_pos)
            )

        if horizontal_tree:
            temp = self.start_pos_x
            self.start_pos_x = self.start_pos_y
            self.start_pos_y = temp

            temp = self.end_pos_x
            self.end_pos_x = self.end_pos_y
            self.end_pos_y = temp


@dataclass
class GhostConnector(Connector):

    is_curved: bool = 1
    is_dashed: bool = 1


@dataclass
class Shape:
    shape_id: str
    shape_content: str
    fill_color: str
    x_pos: float
    y_pos: float
    shape_width: int
    shape_height: int
    template_key: str = "shape"


class NxEdge(NamedTuple):
    subj: any
    obj: any
    pred: any


class NxStringEdge(NxEdge):
    subj: str
    obj: str
    pred: str
