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
        if not self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_WATER_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "The point for the embankment toe waterside is not defined in the Waternet creator settings."
            )

        return True

    def _execute_sand_on_sand_layout(self, ds: DStability) -> List[Tuple[float, float]]:
        raise NotImplementedError()

    def _execute_clay_layout(self, ds: DStability) -> List[Tuple[float, float]]:
        # point A = intersection levee and river level
        intersections = line_polyline_intersections(
            ds.left, self.river_level, ds.right, self.river_level, ds.surface
        )

        if len(intersections) == 0:
            raise AlgorithmExecutionError(
                f"No intersection with the surface and the given river level ({self.river_level}) found."
            )

        Ax, Az = intersections[0]

        # point B.x = A.x + 1
        Bx = Ax + 1.0
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
            if intersections is not None and len(intersections) > 0:
                Fx, Fz = intersections[0]

        return [(Ax, Az), (Bx, Bz), (Cx, Cz), (Dx, Dz), (Ex, Ez), (Fx, Fz)]

    def _execute_sand_on_clay_layout(self, ds: DStability) -> List[Tuple[float, float]]:
        # point A = intersection levee and river level
        intersections = line_polyline_intersections(
            ds.left, self.river_level, ds.right, self.river_level, ds.surface
        )

        if len(intersections) == 0:
            raise AlgorithmExecutionError(
                f"No intersection with the surface and the given river level ({self.river_level}) found."
            )

        Ax, Az = intersections[0]

        # point B.x = A.x
        Bx = Ax
        # point B.z = A.z - 0.5 * (Az - dike toe at polder.z)
        px = ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_WATER_SIDE
        ).x
        pz = ds.z_at(px)[0]
        Bz = Az - 0.5 * (Az - pz)

        # point E = embankment toe land side
        Ex = ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
        ).x
        # E.z = surface + 0.25 * (Az - surface)
        Ez = ds.z_at(Ex)[0] - self.E_offset
        Ez = Ez + 0.25 * (Az - Ez)

        # point C.x = embankment top landside, z = interpolation B-E
        Cx = ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE
        ).x
        Cz = Bz + (Cx - Bx) / (Ex - Bx) * (Ez - Bz)

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

        Dz = Cz + (Dx - Cx) / (Ex - Cx) * (Ez - Cz)
        Fz = self.polder_level
        Fx = Ex + (Ez - Fz) * (Ex - Dx) / (Ez - Dz)

        if Fx > ds.right:
            Fx = ds.right - 0.01
            Fz = self.polder_level

        if len(ds.ditch_points) > 0:
            intersections = line_polyline_intersections(
                ds.left, self.polder_level, ds.right, self.polder_level, ds.ditch_points
            )
            if intersections is not None and len(intersections) > 0:
                Fx, Fz = intersections[0]

        return [(Ax, Az), (Bx, Bz), (Cx, Cz), (Dx, Dz), (Ex, Ez), (Fx, Fz)]

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        abcdef = []  # points A B C D E and F

        if (
            ds.material_layout == MaterialLayoutType.CLAY_EMBANKEMENT_ON_CLAY
            or ds.material_layout == MaterialLayoutType.CLAY_EMBANKEMENT_ON_SAND
        ):
            abcdef = self._execute_clay_layout(ds)
        elif ds.material_layout == MaterialLayoutType.SAND_EMBANKEMENT_ON_CLAY:
            abcdef = self._execute_sand_on_clay_layout(ds)
        else:
            abcdef = self._execute_sand_on_sand_layout(ds)

        # TODO > zorgen dat de freatische lijn niet boven het maaiveld uitkomt tussen punt C en E/F

        plline_points = (
            [(ds.left, self.river_level)] + abcdef + [(ds.right, self.polder_level)]
        )

        ds.set_phreatic_line(plline_points)
        return ds
