from copy import deepcopy
from geolib.geometry import Point
from typing import List, Tuple

from ..dstability import DStability
from .algorithm import Algorithm, AlgorithmInputCheckError, AlgorithmExecutionError
from ...helpers import polyline_polyline_intersections
from ...geometry.characteristic_point import CharacteristicPointType


class AlgorithmPhreaticLine(Algorithm):
    waterlevel_river: float
    waterlevel_polder: float
    waterlevel_offset: float = 0.1
    slope: float = 10
    offset_points: List[Tuple[float, float]] = []

    b_offset: float = 1.0
    c_offset: float = 1.5
    d_offset: float = 0.0
    e_offset: float = 0.0

    def _check_input(self):
        if not self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "No point defined for the embankement top land side"
            )
        if not self.ds.get_characteristic_point(
            CharacteristicPointType.SHOULDER_BASE_LAND_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "No point defined for the shoulder base land side"
            )
        if not self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "No point defined for the embankement toe land side"
            )
        if not self.ds.get_characteristic_point(
            CharacteristicPointType.DITCH_EMBANKEMENT_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "No point defined for the ditch embankement side"
            )
        if not self.ds.get_characteristic_point(
            CharacteristicPointType.DITCH_LAND_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError("No point defined for the ditch land side")

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)
        try:
            self._check_input()
        except Exception as e:
            raise AlgorithmExecutionError(
                f"Could not execute algorithm, got error '{e}'"
            )

        # PHREATIC LINE POINTS
        # left point
        p1 = (ds.left, self.waterlevel_river)
        river_level_ints = ds.surface_intersections([p1, (ds.right, p1[1])])
        if len(river_level_ints) == 0:
            raise AlgorithmExecutionError(
                "No intersections with the riverlevel and the surface found"
            )

        # [A] Intersection of the river water level with the outerslope
        p2 = river_level_ints[0]
        # [B] River water level minus offset, with default offset 1 m, limited by minimum value
        p3 = (p2[0] + 1.0, self.waterlevel_river - self.b_offset)
        # [C] River water level minus offset, with default offset 1.5 m, limited by minimum value
        p4 = (
            self.ds.get_characteristic_point(
                CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE
            ).x,
            self.waterlevel_river - self.c_offset,
        )

        # [E] Surface level at dike toe minus offset, with default offset 0 m.
        cp6x = self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
        ).x
        p6 = (cp6x, self.ds.z_at(cp6x) - self.e_offset)

        # [D] Linear interpolation between point C and point E, unless the user defines an offset Doffset;user with respect to the surface level
        cp5x = self.ds.get_characteristic_point(
            CharacteristicPointType.SHOULDER_BASE_LAND_SIDE
        ).x
        p5 = (cp5x, 0.0)
        if self.d_offset == 0:
            p5[1] = p4[1] + (p5[0] - p4[0]) * (p6[1] - p4[1]) / (p6[0] - p4[0])
        else:
            p5[1] = self.ds.z_at(cp5x) - self.d_offset

        p8 = (self.ds.right, self.waterlevel_polder)

        # [F] Intersection point polder level with ditch
        ditch_intersections = ds.surface_intersections(
            [(self.ds.left, self.waterlevel_polder), p8]
        )
        xl = ds.get_characteristic_point(
            CharacteristicPointType.DITCH_EMBANKEMENT_SIDE
        ).x
        xr = self.ds.get_characteristic_point(CharacteristicPointType.DITCH_LAND_SIDE).x

        ditch_intersections = [
            p for p in ditch_intersections if p[0] >= xl and p[0] <= xr
        ]
        if len(ditch_intersections) == 0:
            raise AlgorithmExecutionError(
                "No intersections with the polder level and the ditch found"
            )
        p7 = ditch_intersections[0]
        
        

        return ds
