from copy import deepcopy

from ...geolib.geometry.one import Point
from .algorithm import Algorithm
from ..dstability import DStability


class AlgorithmExcavation(Algorithm):
    """This algorithm will add a tree load

    Args:
        x (float): location of tree
        depth (float): depth of the excavation
        width (float): width of the excavation
    """

    x: float
    depth: float = 1.0
    width: float = 5.0

    def _check_input(self):
        if (
            self.x - self.width / 2.0 < self.ds.left
            or self.x + self.width / 2.0 > self.ds.right
        ):
            raise ValueError(f"The excavation exceeds the limits of the geometry.")

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        x1 = self.x - self.width / 2.0
        x2 = self.x + self.width / 2.0
        z1 = ds.z_at(x1)[0]
        z2 = ds.z_at(x2)[0]

        excavation_points = [Point(x=x1, z=z1), Point(x=x1, z=z1 - self.depth)]
        # follow the surface from x1 to x2 and get the intermediate points
        surface_points = ds.surface_points_between(x1, x2)
        for p in surface_points:
            excavation_points.append(Point(x=p[0], z=p[1] - self.depth))
        # add the rightmost points
        excavation_points.append(Point(x=x2, z=z2 - self.depth))
        excavation_points.append(Point(x=x2, z=z2))

        # finally.. we can add this excavation using the adjusted geolib version
        ds.model.add_excavation(label="excavation", points=excavation_points)

        return ds
