from copy import deepcopy
from geolib.geometry import Point
from typing import List, Tuple

from ..dstability import DStability
from .algorithm import Algorithm
from ...helpers import polyline_polyline_intersections
from ...geometry.characteristic_point import CharacteristicPointType


class AlgorithmPhreaticLine(Algorithm):
    waterlevel: float
    waterlevel_polder: float
    waterlevel_offset: float = 0.1
    slope: float = 10
    offset_points: List[Tuple[float, float]] = []

    def _check_input(self):
        # do we have a valid x coordinate
        cp_ref = self.ds.get_characteristic_point(
            CharacteristicPointType.REFERENCE_POINT
        )

        if cp_ref is None:
            raise ValueError(
                "AlgorithmPhreaticLine has a geometry without the characteristic point REFERENCE_POINT"
            )

        if cp_ref.x < self.ds.left or cp_ref.x > self.ds.right:
            raise ValueError(
                f"AlgorithmBerm got x reference line at x={cp_ref.x}, which is not within the boundary of the geometry"
            )

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        x_ref = ds.get_characteristic_point(CharacteristicPointType.REFERENCE_POINT).x

        # add leftmost point
        plline = [(ds.left, self.waterlevel)]
        # straight until reference point
        plline.append((x_ref, self.waterlevel))

        # if we have offset points then add them now
        for p in self.offset_points:
            x = x_ref + p[0]
            z = self.waterlevel + p[1]
            plline.append((x, z))

        # follow the surface line and polder_level
        x0 = plline[-1][0]
        z0 = plline[-1][1]

        for point in [p for p in ds.surface if p[0] > x0]:
            dx = point[0] - x0
            z1 = max(z0 - dx / self.slope, self.waterlevel_polder)

            # be sure to stay below the surface
            if z1 > point[1] - self.waterlevel_offset:
                z1 = point[1] - self.waterlevel_offset

            # TODO sloten nog verwerken
            # # but not for ditch points
            # ditches = (
            #     self.calculation_model.get_ditches()
            # )  # list of (x start ditch, x end ditch)

            # for ditch in ditches:
            #     if ditch[0] <= point[0] and point[0] <= ditch[1]:
            #         z1 = self.waterlevel_polder

            plline.append((point[0], round(z1, 2)))
            if point[0] == ds.right:
                break

        ds.set_phreatic_line(plline)

        return ds
