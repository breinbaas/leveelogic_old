from copy import deepcopy
from typing import List, Tuple, Optional

from ...geolib.geometry import Point
from ...deltares.algorithms.algorithm import (
    Algorithm,
    AlgorithmInputCheckError,
    AlgorithmExecutionError,
)
from ...helpers import polyline_polyline_intersections
from ...deltares.dstability import DStability, MaterialLayoutType
from ...geometry.characteristic_point import CharacteristicPointType
from ...helpers import line_polyline_intersections


class AlgorithmPhreaticLineStix(Algorithm):
    river_level: float
    polder_level: float
    B_offset: float = 1.0
    C_offset: float = 1.5
    E_offset: float = 0.0
    D_offset: Optional[float] = None

    def _check_input(self):
        # TODO the stix file must contain the waternet creator settings
        if not self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOP_WATER_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "The point for the embankment top waterside is not defined in the Waternet creator settings."
            )

        if not self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "The point for the embankment top landside is not defined in the Waternet creator settings."
            )

        if not self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "The point for the embankment toe landside is not defined in the Waternet creator settings."
            )

        return True

    def _execute_clay_layout(self, ds: DStability) -> DStability:
        # point A = intersection levee and river level
        intersections = line_polyline_intersections(
            ds.left, self.river_level, ds.right, self.river_level, ds.surface
        )

        if len(intersections) == 0:
            raise AlgorithmExecutionError(
                f"No intersection with the surface and the given river level ({self.river_level}) found."
            )

        Ax, Az = intersections[0]

        # point B.x = embankment top waterside
        Bx = ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOP_WATER_SIDE
        ).x
        # point B.z = A.z - B_offset (defaults to 1.0)
        Bz = Az - self.B_offset

        # point C.x = embankment top landside
        Cx = ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE
        ).x
        # point C.z = A.z - C_offset (defaults to 1.5)
        Cz = Az - self.C_offset

        # point E = embankment toe land side
        Ex = ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
        ).x
        # E.z = surface minus E_offset (defaults to 0.0)
        Ez = ds.z_at(Ex)[0] - self.E_offset

        # point D depends on the shoulder coordinate
        # if not available use the midpoint between C and E
        # if available use that point
        shoulder_point = ds.get_characteristic_point(
            CharacteristicPointType.SHOULDER_BASE_LAND_SIDE
        )
        if shoulder_point.is_valid:
            Dx = shoulder_point.x
        else:
            Dx = (Ex + Cx) / 2.0

        # Dz can be found by lin interpol between C and E
        # or if D_offset is given by surface level at Dx minus the offset
        if self.D_offset is None:
            Dz = Cz + (Dx - Cx) / (Ex - Cx) * (Ez - Cz)
        else:
            Dz = ds.z_at(Dx)[0] - self.D_offset

        # point F is the intersection with the ditch (if available)
        # at the level of the polder_level
        # first assume the location of point F
        # as a lineair extrapolation of the line DE
        Fz = self.polder_level
        Fx = Ex + (Ez - Fz) * (Ex - Dx) / (Ez - Dz)

        if Fx > ds.right:
            Fx = ds.right - 0.01
            Fz = self.polder_level

        if len(ds.ditch_points) > 0:
            intersections = line_polyline_intersections(
                ds.left, self.polder_level, ds.right, self.polder_level, ds.ditch_points
            )
            if len(intersections) > 0:
                Fx, Fz = intersections[0]

        ds.set_phreatic_line(
            (ds.left, self.river_level),
            (Ax, Az),
            (Bx, Bz),
            (Cx, Cz),
            (Dx, Dz),
            (Ex, Ez),
            (Fx, Fz),
            (ds.right, self.polder_level),
        )

    def _execute_sand_layout(self, ds: DStability) -> DStability:
        raise NotImplementedError()

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        if (
            ds.material_layout == MaterialLayoutType.CLAY_EMBANKEMENT_ON_CLAY
            or ds.material_layout == MaterialLayoutType.CLAY_EMBANKEMENT_ON_SAND
        ):
            self._execute_clay_layout(ds)
        else:
            self._execute_sand_layout(ds)

        return ds
