from copy import deepcopy
from math import isnan, nan
import numpy as np
from typing import List, Optional

from ...geolib.geometry import Point
from ..dstability import DStability
from .algorithm import Algorithm, AlgorithmInputCheckError
from ...helpers import polyline_polyline_intersections
from ...geometry.characteristic_point import (
    CharacteristicPoint,
    CharacteristicPointType,
)


class AlgorithmBerm(Algorithm):
    soilcode: str = ""
    slope_top: float = 10.0
    slope_bottom: float = 1.0
    width: float = 0.0
    height: float = 0.0

    fixed_x: float = None
    fixed_z: float = None

    fill_ditch: bool = False
    ditch_soilcode: str = None

    def _check_input(self):
        # if we are using the algorithm to not only fill the ditch do we have this soilcode for the berm?
        if self.width > 0 or self.fixed_x is not None:
            if not self.ds.has_soilcode(self.soilcode):
                raise AlgorithmInputCheckError(
                    f"AlgorithmBermWSBD got an invalid soilcode '{self.soilcode}'"
                )

            # We need the embankment toe char point
            embankement_toe_land_side = self.ds.get_characteristic_point(
                CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
            )
            if (
                embankement_toe_land_side is None
                or not embankement_toe_land_side.is_valid
            ):
                raise AlgorithmInputCheckError(
                    "The given stix file has no waternet creator settings where the embankment toe land side point is set which is required for this algorithm to run."
                )

        # if we want to fill the ditch we need to know the ditch points
        if self.fill_ditch:
            ditch_embankment_side = self.ds.get_characteristic_point(
                CharacteristicPointType.DITCH_EMBANKEMENT_SIDE
            )
            if (ditch_embankment_side) is None or not ditch_embankment_side.is_valid:
                raise AlgorithmInputCheckError(
                    "You want to fill the ditch but the ditch embankment side point is not given."
                )

            ditch_land_side = self.ds.get_characteristic_point(
                CharacteristicPointType.DITCH_LAND_SIDE
            )
            if (ditch_land_side) is None or not ditch_land_side.is_valid:
                raise AlgorithmInputCheckError(
                    "You want to fill the ditch but the ditch land side point is not given."
                )

        # # Ditch information, maybe for later
        # if (
        #     not self.ds.model.datastructure.waternetcreatorsettings[
        #         0
        #     ].DitchCharacteristics.DitchEmbankmentSide
        #     == "NaN"
        # ):
        #     self.ditch_embankement_side = float(
        #         self.ds.model.datastructure.waternetcreatorsettings[
        #             0
        #         ].DitchCharacteristics.DitchEmbankmentSide
        #     )

        # MAYBE FOR PL REASONS
        # self.ditch_bottom_embankement_side = float(
        #     self.ds.model.datastructure.waternetcreatorsettings[
        #         0
        #     ].DitchCharacteristics.DitchBottomEmbankmentSide
        # )
        # self.ditch_bottom_land_side = float(
        #     self.ds.model.datastructure.waternetcreatorsettings[
        #         0
        #     ].DitchCharacteristics.DitchBottomLandSide
        # )
        # if (
        #     not self.ds.model.datastructure.waternetcreatorsettings[
        #         0
        #     ].DitchCharacteristics.DitchLandSide
        #     == "NaN"
        # ):
        #     self.ditch_land_side = float(
        #         self.ds.model.datastructure.waternetcreatorsettings[
        #             0
        #         ].DitchCharacteristics.DitchLandSide
        #     )

        # if self.fill_ditch:
        #     if isnan(self.ditch_embankement_side) or isnan(self.ditch_land_side):
        #         raise AlgorithmInputCheckError(
        #             "Cannot fill the ditch since the ditch embankement side and/or the ditch land side points are missing."
        #         )
        #     if self.ditch_soilcode is None:
        #         raise AlgorithmInputCheckError(
        #             "Cannot fill the ditch since the ditch soilcode is not set."
        #         )
        #     if not self.ds.has_soilcode(self.ditch_soilcode):
        #         raise AlgorithmInputCheckError(
        #             f"Cannot fill the ditch since the ditch soilcode ('{self.ditch_soilcode}') is not valid."
        #         )

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        embankement_toe_land_side = self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
        ).x

        if self.fill_ditch:
            ditch_embankement_side = self.ds.get_characteristic_point(
                CharacteristicPointType.DITCH_EMBANKEMENT_SIDE
            ).x
            ditch_land_side = self.ds.get_characteristic_point(
                CharacteristicPointType.DITCH_LAND_SIDE
            ).x

            fp1 = self.ds.get_closest_point_from_x(ditch_embankement_side)
            fp2 = self.ds.get_closest_point_from_x(ditch_land_side)
            fp_points = [fp1, fp2] + self.ds.surface_points_between(fp1[0], fp2[0])[
                ::-1
            ]
            ds.add_layer(
                fp_points,
                self.ditch_soilcode,
                label="ditch fill",
                scenario_index=ds.current_scenario_index,
                stage_index=ds.current_stage_index,
            )

        # the algorithm could be used to only fill the ditch
        # in this case the height width can be zero and the fixed coords not set
        if self.fixed_x is None and self.width <= 0.0:
            return ds

        p1 = (
            embankement_toe_land_side,
            ds.z_at(embankement_toe_land_side),
        )
        if self.fixed_x is not None and self.fixed_z is not None:
            # the topright point of the berm is defined so now find out the intersections based on the slopes
            p3 = (
                ds.left,
                self.fixed_z + (self.fixed_x - ds.left) / self.slope_top,
            )
            p4 = (
                ds.right,
                self.fixed_z - (ds.right - embankement_toe_land_side) / self.slope_top,
            )
        elif self.width > 0 and self.height > 0:
            # toe of the levee

            # toe of the levee plus the initial height
            p2 = (embankement_toe_land_side, p1[1] + self.height)
            # left most points based on slope s1
            p3 = (
                ds.left,
                p2[1] + (embankement_toe_land_side - ds.left) / self.slope_top,
            )
            #  rightmost point based on slope s1
            p4 = (
                ds.right,
                p2[1] - (ds.right - embankement_toe_land_side) / self.slope_top,
            )

        else:
            raise ValueError("No valid berm option given")

        # get all intersections with the top of the berm
        intersections = polyline_polyline_intersections([p3, p4], ds.surface)

        # get all intersections on the left side of the toe of the levee
        left_intersections = [p for p in intersections if p[0] < p1[0]]
        # if we have no intersections then we do not intersect the surface on the left side
        if len(left_intersections) == 0:
            raise ValueError(
                "No intersections on the left side of x_toe, can not create a berm"
            )
        # FIRST POINT OF BERM -> start of berm (left side)
        pA = left_intersections[-1]

        if self.fixed_x is not None:
            pB = (self.fixed_x, self.fixed_z)
        else:
            pB = (pA[0] + self.width, pA[1] - self.width / self.slope_top)
        p5 = (
            ds.right,
            pB[1] - (ds.right - pB[0]) / self.slope_bottom,
        )

        intersections = polyline_polyline_intersections([pB, p5], ds.surface)
        # if we have no intersections then we do not intersect the surface on the left side
        if len(intersections) == 0:
            raise ValueError(
                "No intersections between point B and p5, cannot create berm"
            )
        pC = intersections[-1]

        intersections = polyline_polyline_intersections([pA, pB, pC], ds.surface)
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
            points += ds.surface_points_between(p1[0], p2[0])[::-1]

            ds.add_layer(
                points,
                self.soilcode,
                scenario_index=ds.current_scenario_index,
                stage_index=ds.current_stage_index,
            )

        return ds
