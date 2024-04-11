from copy import deepcopy
from typing import List, Tuple, Optional

from ...geolib.geometry import Point
from .algorithm import (
    Algorithm,
    AlgorithmInputCheckError,
    AlgorithmExecutionError,
)
from ...helpers import polyline_polyline_intersections
from ..dstability import DStability, MaterialLayoutType
from ...geometry.characteristic_point import CharacteristicPointType
from ...helpers import line_polyline_intersections


class AlgorithmPhreaticLine(Algorithm):
    river_level: float
    polder_level: float
    B_offset: Optional[float] = None
    C_offset: Optional[float] = None
    E_offset: Optional[float] = None
    D_offset: Optional[float] = None
    surface_offset: float = 0.01
    phreatic_level_embankment_top_waterside: Optional[float] = None
    phreatic_level_embankment_top_landside: Optional[float] = None

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

    def _execute(self) -> DStability:
        if self.add_as_new_stage:
            ds = self.ds
            ds.add_stage()
        else:
            ds = deepcopy(self.ds)

        # height River waterlevel - Dike toe level
        x = self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
        ).x
        h = self.river_level - ds.z_at(x)

        # point A - (ALL) - Intersection of the river water level with the outer slope
        intersections = line_polyline_intersections(
            ds.left, self.river_level, ds.right, self.river_level, ds.surface
        )

        if len(intersections) == 0:
            raise AlgorithmExecutionError(
                f"No intersection with the surface and the given river level ({self.river_level}) found."
            )

        Ax, Az = intersections[0]

        # Point E is needed for interpolation so we calculate this first
        # Point E1 (CLAY DIKE) Surface level at dike toe minus offset, with default offset 0 m
        Ex = ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
        ).x
        Ez1 = ds.z_at(Ex)
        if self.E_offset is not None:
            # user defined offset (if no user defined offset the the default offset equals zero)
            Ez1 -= self.E_offset

        # Point E2 (SAND ON CLAY) Surface level at dike toe minus offset, with default offset −0.25 × (river level - polder level).
        Ez2 = ds.z_at(Ex)
        if self.E_offset is None:
            Ez2 += 0.25 * h
        else:
            Ez2 += self.E_offset

        # Point E3 (SAND ON CLAY) = E2 (SAND ON SAND)
        Ez3 = Ez2

        # Point E must be equal to or above polder level
        Ez1 = max(self.polder_level, Ez1)
        Ez2 = max(self.polder_level, Ez2)
        Ez3 = max(self.polder_level, Ez3)

        # Point B1 (CLAY DIKE) River water level minus offset, with default offset 1 m, limited by minimum value ZB;initial, see section 3.3.1.2.
        Bx1 = Ax + 1.0
        if self.phreatic_level_embankment_top_waterside is not None:
            # user defined pl
            Bz1 = self.phreatic_level_embankment_top_waterside
        elif self.B_offset is not None:
            # user defined offset
            Bz1 = self.river_level - self.B_offset
        else:  # default offset
            Bz1 = self.river_level - 1.0

        # Point B2 (SAND ON CLAY) River water level minus offset, with default offset 0.5 × (river level - dike toe polder level), limited by minimum value ZB;initial, see section 3.3.1.2.
        Bx2 = Ax + 0.001
        if self.phreatic_level_embankment_top_waterside is not None:
            # user defined pl
            Bz2 = self.phreatic_level_embankment_top_waterside
        elif self.B_offset is not None:
            # user defined offset
            Bz2 = self.river_level - self.B_offset
        else:
            # default offset
            Bz2 = self.river_level - 0.5 * h

        # Point B3 (SAND ON SAND) Linear interpolation between point A and point E, limited by minimum value ZB;initial, see section 3.3.1.2.
        Bx3 = Ax + 0.001
        if self.phreatic_level_embankment_top_waterside is not None:
            # user defined pl
            Bz3 = self.phreatic_level_embankment_top_waterside
        else:
            # lineair interpolation
            Bz3 = Az + (Bx3 - Ax) / (Ex - Ax) * (Ez3 - Az)

        # Point C1 (CLAY DIKE) River water level minus offset, with default offset 1.5 m, limited by minimum value ZC;initial, see section 3.3.1.2.
        Cx = ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE
        ).x
        if self.phreatic_level_embankment_top_landside is not None:
            Cz1 = self.phreatic_level_embankment_top_landside
        elif self.C_offset is not None:
            Cz1 = self.river_level - self.C_offset
        else:
            Cz1 = self.river_level - 1.5

        # Point C2 (SAND ON CLAY) Linear interpolation between point B and point E, limited by minimum value ZC;initial, see section 3.3.1.2.
        if self.phreatic_level_embankment_top_landside is not None:
            Cz2 = self.phreatic_level_embankment_top_landside
        else:
            Cz2 = Bz2 + (Cx - Bx2) / (Ex - Bx2) * (Ez2 - Bz2)

        # Point C3 (SAND ON SAND) Linear interpolation between point A and point E, limited by minimum value ZC;initial, see section 3.3.1.2.
        if self.phreatic_level_embankment_top_landside is not None:
            Cz3 = self.phreatic_level_embankment_top_landside
        else:
            Cz3 = Az + (Cx - Ax) / (Ex - Ax) * (Ez3 - Az)

        shoulder_point = ds.get_characteristic_point(
            CharacteristicPointType.SHOULDER_BASE_LAND_SIDE
        )
        if shoulder_point.is_valid:
            Dx = shoulder_point.x

            # Point D1 (CLAY DIKE) Linear interpolation between point C and point E, unless the user defines an offset Doffset;user with respect to the surface level.
            if self.D_offset is not None:
                Dz1 = ds.z_at(Dx) - self.D_offset
            else:
                Dz1 = Cz1 + (Dx - Cx) / (Ex - Cx) * (Ez1 - Cz1)

            # Point D2 (SAND ON CLAY) Linear interpolation between point B and point E, unless the user defines an offset Doffset;user with respect to the surface level.
            if self.D_offset is not None:
                Dz2 = ds.z_at(Dx) - self.D_offset
            else:
                Dz2 = Bz2 + (Dx - Bx2) / (Ex - Bx2) * (Ez2 - Bz2)

            # Point D3 (SAND ON SAND) Linear interpolation between point A and point E, unless the user defines an offset Doffset;user with respect to the surface level
            if self.D_offset is not None:
                Dz3 = ds.z_at(Dx) - self.D_offset
            else:
                Dz3 = Az + (Dx - Ax) / (Ex - Ax) * (Ez3 - Az)
        else:  # add D as lin interpolated point between C and E
            Dx = (Ex - Cx) / 2.0
            Dz1 = (Ez1 - Cz1) / 2.0
            Dz2 = (Ez2 - Cz2) / 2.0
            Dz3 = (Ez3 - Cz3) / 2.0

        # Point D must be equal to or above polder level
        Dz1 = max(self.polder_level, Dz1)
        Dz2 = max(self.polder_level, Dz2)
        Dz3 = max(self.polder_level, Dz3)

        # Point D must be equal to or below point C
        Dz1 = min(Cz1, Dz1)
        Dz2 = min(Cz2, Dz2)
        Dz3 = min(Cz3, Dz3)

        # Point E must be equal to or below point D
        # TODO > what if we adjust this value but E is already used for interpolation
        Ez1 = min(Dz1, Ez1)
        Ez2 = min(Dz2, Ez2)
        Ez3 = min(Dz3, Ez3)

        # Point F Intersection point polder level with ditch (is determined automatically)
        Fz = self.polder_level
        if len(ds.ditch_points) > 0:  # with ditch find intersection
            intersections = line_polyline_intersections(
                ds.left, self.polder_level, ds.right, self.polder_level, ds.ditch_points
            )
            if intersections is not None and len(intersections) > 0:
                Fx1, _ = intersections[0]
                Fx2 = Fx1
                Fx3 = Fx1
        else:
            # If no ditch, lin extrapolation to polder level from C to E
            Fx1 = Ex + (Ez1 - Fz) * (Ex - Cx) / (Ez1 - Cz1)
            Fx2 = Ex + (Ez2 - Fz) * (Ex - Cx) / (Ez2 - Cz2)
            Fx3 = Ex + (Ez3 - Fz) * (Ex - Cx) / (Ez3 - Cz3)

        if (
            self.ds.material_layout == MaterialLayoutType.CLAY_EMBANKEMENT_ON_CLAY
            or self.ds.material_layout == MaterialLayoutType.CLAY_EMBANKEMENT_ON_SAND
        ):
            abcdef = [[Ax, Az], [Bx1, Bz1], [Cx, Cz1], [Dx, Dz1], [Ex, Ez1], [Fx1, Fz]]
        elif self.ds.material_layout == MaterialLayoutType.SAND_EMBANKEMENT_ON_CLAY:
            abcdef = [[Ax, Az], [Bx2, Bz2], [Cx, Cz2], [Dx, Dz2], [Ex, Ez2], [Fx2, Fz]]
        elif self.ds.material_layout == MaterialLayoutType.SAND_EMBANKEMENT_ON_SAND:
            abcdef = [[Ax, Az], [Bx3, Bz3], [Cx, Cz3], [Dx, Dz3], [Ex, Ez3], [Fx3, Fz]]
        else:
            raise ValueError(f"Unknown material layout '{self.ds.material_layout}'")

        # Make sure the phreatic line does not exceed the surface
        # Between A and F
        # 1. get all surface points
        surface_points = [
            p for p in ds.surface if p[0] > abcdef[0][0] and p[0] < abcdef[-1][0]
        ]
        # 2. get all intersections between surface and pl line
        intersections = [
            p
            for p in polyline_polyline_intersections(abcdef, ds.surface)
            if p[0] > Ax and p[0] < Ex
        ]
        # 3. merge x coords
        check_points = sorted([p[0] for p in surface_points + intersections])

        # create the final points, start with the leftmost point
        final_points = [[self.ds.left, self.river_level], abcdef[0]]
        # now add the points
        for x in check_points:
            for i in range(1, len(abcdef)):
                x1, z1 = abcdef[i - 1]
                x2, z2 = abcdef[i]
                if x1 <= x and x <= x2:
                    z_pl = z1 + (x - x1) / (x2 - x1) * (z2 - z1)
                    z_surface = ds.z_at(x)

                    if z_pl > z_surface - 0.01:
                        z_pl = z_surface - 0.01

                    final_points.append([x, z_pl])
                    break

        # add F and the rightmost point
        final_points += [abcdef[-1], [ds.right, self.polder_level]]

        # # from point C to point F we want to be sure that all points are below the surface
        # plpoints = [[ds.left, self.river_level]] + abcdef[:2]

        # # first insert all the points based on linear interpolation
        # # without checking the height
        # # TODO > immediately check if the point is above the surface line and ajust accordingly
        # for i in range(2, len(abcdef) - 1):
        #     p1 = abcdef[i]
        #     p2 = abcdef[i + 1]

        #     plpoints.append(p1)
        #     for p in ds.surface:
        #         if p1[0] < p[0] and p[0] < p2[0]:
        #             z_interpolated = p1[1] + (p[0] - p1[0]) / (p2[0] - p1[0]) * (
        #                 p2[1] - p1[1]
        #             )
        #             plpoints.append([p[0], z_interpolated])

        #     if i == len(abcdef) - 2:
        #         plpoints.append(p2)

        # # now check the height for all points between C and (excluding) F
        # # TODO > als de freatische lijn de surface snijdt dan moet het snijpunt wel toegevoegd
        # # zie pl_sand_on_clay_solution
        # for i in range(len(plpoints)):
        #     if plpoints[i][0] > abcdef[2][0] and plpoints[i][0] < abcdef[-1][0]:
        #         z_surface = ds.z_at(plpoints[i][0])
        #         if plpoints[i][1] > z_surface - self.surface_offset:
        #             plpoints[i][1] = z_surface - self.surface_offset
        #         # but don't go higher than the previous point
        #         if i > 0 and plpoints[i][1] > plpoints[i - 1][1]:
        #             plpoints[i][1] = plpoints[i - 1][1]

        # plpoints.append([ds.right, self.polder_level])

        ds.set_phreatic_line(final_points)
        return ds
