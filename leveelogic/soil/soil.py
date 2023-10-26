from typing import Tuple

from ..models.datamodel import DataModel
from ..helpers import hex_color_to_rgb_tuple


class Soil(DataModel):
    """Class to store basic soil data"""

    code: str
    color: str
    y_dry: float
    y_sat: float
    cohesion: float
    friction_angle: float

    def color_as_rgb(self) -> Tuple[float, float, float]:
        return hex_color_to_rgb_tuple(self.color)
