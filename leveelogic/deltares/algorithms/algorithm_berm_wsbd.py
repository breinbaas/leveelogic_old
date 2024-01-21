from copy import deepcopy
from geolib.geometry import Point
from math import isnan, nan
import numpy as np
from typing import List

from ..dstability import DStability
from .algorithm import Algorithm, AlgorithmInputCheckError
from ...helpers import polyline_polyline_intersections
from ...geometry.characteristic_point import CharacteristicPointType


class AlgorithmBermWSBD(Algorithm):
    soilcode: str
    slope_top: float
    slope_bottom: float
    width: float
    height: float

    embankement_toe_land_side: float = nan
    # ditch_embankement_side: float = nan
    # ditch_bottom_embankement_side: float = nan
    # ditch_bottom_land_side: float = nan
    # ditch_land_side: float = nan

    def _check_input(self):
        # do we have this soilcode
        if not self.ds.has_soilcode(self.soilcode):
            raise AlgorithmInputCheckError(
                f"AlgorithmBermWSBD got an invalid soilcode '{self.soilcode}'"
            )

        # do we have the toe char points
        self.embankement_toe_land_side = (
            self.ds.model.datastructure.waternetcreatorsettings[
                0
            ].EmbankmentCharacteristics.EmbankmentToeLandSide
        )

        if isnan(self.embankement_toe_land_side):
            raise AlgorithmInputCheckError(
                "The given stix file has no waternet creator settings where the embankement toe land side point is set which is required for this algorithm to run."
            )

        # # Ditch information, maybe for later
        # self.ditch_embankement_side = (
        #     self.ds.model.datastructure.waternetcreatorsettings[
        #         0
        #     ].DitchCharacteristics.DitchEmbankmentSide
        # )
        # self.ditch_bottom_embankement_side = (
        #     self.ds.model.datastructure.waternetcreatorsettings[
        #         0
        #     ].DitchCharacteristics.DitchBottomEmbankmentSide
        # )
        # self.ditch_bottom_land_side = (
        #     self.ds.model.datastructure.waternetcreatorsettings[
        #         0
        #     ].DitchCharacteristics.DitchBottomLandSide
        # )
        # self.ditch_land_side = self.ds.model.datastructure.waternetcreatorsettings[
        #     0
        # ].DitchCharacteristics.DitchLandSide

    def _execute(self) -> DStability:
        self._check_input()
        ds = deepcopy(self.ds)

        # toe of the levee
        p1 = (
            self.embankement_toe_land_side,
            self.ds.z_at(self.embankement_toe_land_side)[0],
        )
        # toe of the levee plus the initial height
        p2 = (self.embankement_toe_land_side, p1[1] + self.height)
        # left most points based on slope s1
        p3 = (
            self.ds.left,
            p2[1] + (self.embankement_toe_land_side - self.ds.left) / self.slope_top,
        )
        #  rightmost point based on slope s1
        p4 = (
            self.ds.right,
            p2[1] - (self.ds.right - self.embankement_toe_land_side) / self.slope_top,
        )

        # get all intersections with the top of the berm
        intersections = polyline_polyline_intersections([p3, p4], self.ds.surface)

        # get all intersections on the left side of the toe of the levee
        left_intersections = [p for p in intersections if p[0] < p1[0]]
        # if we have no intersections then we do not intersect the surface on the left side
        if len(left_intersections) == 0:
            raise ValueError(
                "No intersections on the left side of x_toe, can not create a berm"
            )
        # FIRST POINT OF BERM -> start of berm (left side)
        pA = left_intersections[-1]
        pB = (pA[0] + self.height, pA[1] - self.height / self.slope_top)
        p5 = (
            self.ds.right,
            pB[1] - (self.ds.right - pB[0]) / self.slope_bottom,
        )

        intersections = polyline_polyline_intersections([pB, p5], self.ds.surface)
        # if we have no intersections then we do not intersect the surface on the left side
        if len(intersections) == 0:
            raise ValueError(
                "No intersections between point B and p5, cannot create berm"
            )
        pC = intersections[-1]

        intersections = polyline_polyline_intersections([pA, pB, pC], self.ds.surface)
        intersections = [(round(p[0], 3), round(p[1], 3)) for p in intersections]

        if not (round(pA[0], 3), round(pA[1], 3)) in intersections:
            intersections.insert(0, pA)
        if not (round(pC[0], 3), round(pC[1], 3)) in intersections:
            intersections.append(pC)

        # TODO theoretically this check can go wrong if the right point of a part of the berm
        # meets the left point of the next berm (so if they share a geometry point)
        # this actually happens in the test case but in practice this can be ignored
        # it could be solved in code though.. that's why this is a TODO
        if len(intersections) % 2 != 0:
            raise ValueError(
                "The berm continues outside of the right limit of the geometry, cannot create berm"
            )

        for i in range(0, len(intersections), 2):
            # get the left and right point of the berm
            p1 = intersections[i]
            p2 = intersections[i + 1]

            # check if we need to add the knikpunt of the berm
            if p1[0] < pB[0] and pB[0] < p2[0]:
                points = [p1, pB, p2]
            else:
                points = [p1, p2]

            # now follow the surface back to p1
            points += self.ds.surface_points_between(p1[0], p2[0])[::-1]

            # convert to deltares points
            new_layer_points = [Point(x=p[0], z=p[1]) for p in points]
            ds.model.add_layer(new_layer_points, self.soilcode)

        return ds
