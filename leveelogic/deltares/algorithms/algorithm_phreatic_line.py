from copy import deepcopy
from typing import List, Tuple

from ...geolib.geometry import Point
from ...deltares.algorithms.algorithm import Algorithm
from ...helpers import polyline_polyline_intersections
from ...deltares.dstability import DStability


class AlgorithmPhreaticLine(Algorithm):
    x_ref: float
    waterlevel: float
    waterlevel_polder: float
    waterlevel_offset: float = 0.1
    slope: float = 10
    offset_points: List[Tuple[float, float]] = []

    def _check_input(self):
        return True

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        # check if we have a ditch
        # if so we want to ignore the code to stay below the surface
        # between the start and end of the ditch
        ignore_from_x = -9999
        ignore_until_x = -9999
        if len(ds.ditch_points) > 0:
            ignore_from_x = ds.ditch_points[0][0]
            ignore_until_x = ds.ditch_points[-1][0]

        # add leftmost point
        plline = [(ds.left, self.waterlevel)]
        # straight until reference point
        plline.append((self.x_ref, self.waterlevel))

        # if we have offset points then add them now
        for p in self.offset_points:
            x = self.x_ref + p[0]
            z = self.waterlevel + p[1]
            plline.append((x, z))

        # follow the surface line and polder_level
        x0 = plline[-1][0]
        z0 = plline[-1][1]

        for point in [p for p in ds.surface if p[0] > x0]:
            dx = point[0] - x0
            z1 = max(z0 - dx / self.slope, self.waterlevel_polder)

            # be sure to stay below the surface
            if point[0] < ignore_from_x or point[0] > ignore_until_x:
                if z1 > point[1] - self.waterlevel_offset:
                    z1 = point[1] - self.waterlevel_offset
            else:
                z1 = self.waterlevel_polder

            plline.append((point[0], round(z1, 2)))
            if point[0] == ds.right:
                break

        ds.set_phreatic_line(plline)

        return ds
