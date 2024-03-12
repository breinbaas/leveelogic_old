from copy import deepcopy

from ...geolib.models.dstability.loads import TreeLoad, LineLoad
from ...geolib.geometry.one import Point
from .algorithm import Algorithm
from ..dstability import DStability


class AlgorithmTree(Algorithm):
    """This algorithm will add a tree load

    Args:
        x (float): location of tree
        height (float): height of the tree, defaults to 5m
        wind_force (float): wind force on the tree, defaults to 10 kN/m (+ = towards the right of the geometry)
        width_of_root_zone (float): width of the root zone, defaults to 5m
        load (float): point load at bottom of tree [kN]
        angle (float): angle of (load) distribution, defaults to 0 degrees
    """

    x: float
    tree_height: float = 5.0
    width_of_root_zone: float = 5.0
    load: float = 0.0
    load_angle: float = 0.0
    wind_force: float = 10  # positive is towards polder (right)
    angle_of_distribution: float = 0

    def _check_input(self):
        if (
            self.x - self.width_of_root_zone / 2.0 < self.ds.left
            or self.x + self.width_of_root_zone / 2.0 > self.ds.right
        ):
            raise ValueError(
                f"The tree location with the given width of the root zone exceeds the limits of the geometry."
            )

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)
        z = round(ds.z_at(self.x)[0], 2)
        ds.model.add_load(
            TreeLoad(
                tree_top_location=Point(x=self.x, z=z + self.tree_height),
                wind_force=self.wind_force,
                width_of_root_zone=self.width_of_root_zone,
                angle_of_distribution=self.angle_of_distribution,
            )
        )

        if self.load > 0.0:
            ds.model.add_load(
                LineLoad(
                    location=Point(x=self.x, z=z),
                    magnitude=self.load,
                    angle=self.load_angle,
                    angle_of_distribution=self.angle_of_distribution,
                )
            )

        return ds
