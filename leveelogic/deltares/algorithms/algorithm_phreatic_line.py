from copy import deepcopy
from geolib.geometry import Point
from typing import List, Tuple

from ..dstability import DStability
from .algorithm import Algorithm
from ...helpers import polyline_polyline_intersections


class AlgorithmPhreaticLine(Algorithm):
    x_reference: float
    waterlevel: float
    waterlevel_polder: float
    waterlevel_offset: float = 0.1
    slope: float = 10
    offset_points: List[Tuple[float, float]] = []

    def _check_input(self):
        # do we have a valid x coordinate
        if self.x_reference < self.ds.left or self.x_reference > self.ds.right:
            raise ValueError(
                f"AlgorithmBerm got x_reference ({self.x_reference}) that is not within the boundary of the geometry"
            )

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        return ds
