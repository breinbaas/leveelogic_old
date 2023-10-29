from copy import deepcopy
from geolib.geometry import Point

from ..dstability import DStability
from .algorithm import Algorithm
from ...helpers import polyline_polyline_intersections
from ...geometry.characteristic_point import CharacteristicPointType


class AlgorithmBerm(Algorithm):
    soilcode: str
    slope_top: float
    slope_bottom: float
    initial_width: float
    initial_height: float

    def _check_input(self):
        # do we have this soilcode
        if not self.ds.has_soilcode(self.soilcode):
            raise ValueError(f"AlgorithmBerm got an invalid soilcode '{self.soilcode}'")

        # do we have the toe char points
        cp = self.ds.get_characteristic_point(CharacteristicPointType.TOE_RIGHT)
        if cp is None:
            raise ValueError(
                "AlgorithmBerm got a model without the characteristic point of the toe of the levee"
            )

        # do we have a valid x coordinate
        if cp.x < self.ds.left or cp.x > self.ds.right:
            raise ValueError(
                f"AlgorithmBerm got x coordinate of the left toe point at ({cp.x}) that is not within the boundary of the geometry"
            )

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        xt = self.ds.get_characteristic_point(CharacteristicPointType.TOE_RIGHT).x
        wi = self.initial_width
        hi = self.initial_height

        # toe of the levee
        p1 = (xt, self.ds.z_at(xt)[0])
        # toe of the levee plus the initial height
        p2 = (xt, p1[1] + hi)
        # left most points based on slope s1
        p3 = (self.ds.left, p2[1] + (xt - self.ds.left) / self.slope_top)
        #  rightmost point based on slope s1
        p4 = (self.ds.right, p2[1] - (self.ds.right - xt) / self.slope_top)

        # get all intersections with the top of the berm
        intersections = polyline_polyline_intersections([p3, p4], self.ds.surface)

        # remove all intersections where x > p1.x because we want the intersections on the left side
        left_intersections = [p for p in intersections if p[0] < p1[0]]
        # if we have no intersections then we do not intersect the surface on the left side
        if len(left_intersections) == 0:
            raise ValueError(
                "No intersections on the left side of x_toe, can not create a berm"
            )
        # start of berm (left side) # FIRST POINT OF BERM
        p5 = left_intersections[-1]

        # now get the intersections on the right side
        right_intersections = [p for p in intersections if p[0] > p1[0]]

        # end of the berm (right side) # SECOND POINT OF BERM
        p6 = (p5[0] + wi, p5[1] - wi / self.slope_top)

        # check for any surface intersections between p5 and p6
        surface_intersections = [
            p for p in intersections if p[0] > p5[0] and p[0] < p6[0]
        ]
        if len(surface_intersections) > 0:
            raise NotImplementedError(
                "Got intersections with the surface between the topleft and topright point of the berm, cannot deal with that right now..."
            )

        # now create a line from the topright point to the surface
        p7 = (self.ds.right, p6[1] - (self.ds.right - p6[0]) / self.slope_bottom)

        intersections = polyline_polyline_intersections([p6, p7], self.ds.surface)
        if len(intersections) == 0:
            raise ValueError(
                "No intersections between the topright point of the berm and the surface, can not create a berm"
            )

        p8 = intersections[0]

        # now create the layer points (we need to use the Point class for this)
        new_layer_points = [Point(x=p[0], z=p[1]) for p in [p5, p6, p8]]

        # we also need to add the bottom of the layer
        new_layer_points += [
            Point(x=p[0], z=p[1])
            for p in self.ds.surface_points_between(p5[0], p8[0])[::-1]
        ]
        ds.model.add_layer(new_layer_points, self.soilcode)

        return ds
