from typing import List
from copy import deepcopy
import numpy as np

from ...geolib.models.dstability.internal import PersistablePoint
from .algorithm import Algorithm
from ..dstability import DStability


class AlgorithmFCPhreaticLineWSBD(Algorithm):
    """This algorithm will calculate a fragility curve based on the phreatic line

    Args:
        river level: float, waterlevel in the river


    Returns:
        List[DStability]: a list of DStability object with different phreatic lines
    """

    max_level: float
    min_level: float
    step: float

    log: List[str] = []

    def _check_input(self):
        pass

    def _execute_multiple_results(self) -> List[DStability]:
        result = []

        for z in np.arange(self.min_level, self.max_level + self.step * 0.5, self.step):
            ds = deepcopy(self.ds)
            # get the dx, dz between point 2 and 3 of the phreatic line
            p2 = ds.phreatic_line.Points[1]
            p3 = ds.phreatic_line.Points[2]
            p6 = ds.phreatic_line.Points[5]
            dx = float(p3.X) - float(p2.X)
            dz = float(p3.Z) - float(p2.Z)

            surface_intersections = ds.surface_intersections(
                [(ds.left, z), (ds.right, z)]
            )

            if len(surface_intersections) == 0:
                self.log.append("No surface intersection at z={z:.2f}")
                continue

            # first point simply get the z value
            ds.phreatic_line.Points[0] = PersistablePoint(X=ds.left, Z=z)
            # the second point is placed on the intersection with the surface at level z
            ds.phreatic_line.Points[1] = PersistablePoint(
                X=surface_intersections[0][0], Z=z
            )

            # the third point gets the same dx / dz as the original calculation
            # but the z value must not be lower then point 6.z (embankement toe)
            ds.phreatic_line.Points[2] = PersistablePoint(
                X=float(ds.phreatic_line.Points[1].X) + dx,
                Z=max(float(ds.phreatic_line.Points[1].Z) + dz, float(p6.Z)),
            )

            # points 4 and 5 move close to point 6 and loose their function
            ds.phreatic_line.Points[3].X = float(p6.X) - 0.02
            ds.phreatic_line.Points[3].Z = float(p6.Z)
            ds.phreatic_line.Points[4].X = float(p6.X) - 0.01
            ds.phreatic_line.Points[4].Z = float(p6.Z)

            # PL3 is always created if the Waternet Creator has been used
            try:
                pl3 = ds.get_headline_by_label("Stijghoogtelijn 3 (PL3)")
            except Exception as e:
                self.log.append(f"Error getting the PL3 headline; '{e}'")
                continue

            try:
                assert len(pl3.Points) >= 4
            except Exception as e:
                self.log.append(
                    f"The PL3 in this model does not have the required 4 points"
                )
                continue

            pl3_p1 = pl3.Points[0]
            pl3_p2 = pl3.Points[1]
            pl3_p3 = pl3.Points[2]
            pl3_p4 = pl3.Points[3]

            # the first point of PL3 simply gets the z value
            pl3_p1.Z = z
            # the second point will be placed at x intersection surface minus the original
            # distance between the old intersection of the surface and the second point on PL3
            pl_dx = float(pl3.Points[2].X) - float(pl3.Points[1].X)
            pl3_p2.X = float(ds.phreatic_line.Points[1].X) - pl_dx
            pl3_p2.Z = z

            # the third point will have the same distance between the x coords of the original
            # PL3 point 2 and 3 coords
            pl3_p3.X = float(pl3_p2.X) + pl_dx
            # the z coordinate will have the same distance between the original z coords
            # PL3 points 2 and 3
            pl3_p3.Z = z + (
                float(self.ds.phreatic_line.Points[2].Z)
                - float(self.ds.phreatic_line.Points[0].Z)
            )
            # and finally point 4 will have the same z coord as pl3.z
            pl3_p4.Z = pl3_p3.Z

            # if there are more points on the line after point 3 they will all be punt close to the
            # last point on PL3 (and loose their function)

            # now set these as the new coords
            org_points = [
                [p[0], p[1]]
                for p in ds.get_headline_coordinates("Stijghoogtelijn 3 (PL3)")
            ]  # convert to list

            # if we have more than 4 points move these close to the last point
            # and use the z coordinate of pl3_p3
            for i in range(len(org_points) - 2, 3, -1):
                org_points[i][0] = org_points[len(org_points) - 1][0] - 0.01 * (
                    len(org_points) - i - 1  # move each point 1cm to the left
                )
                org_points[i][1] = float(pl3_p3.Z)
            org_points[-1][1] = float(pl3_p3.Z)

            new_points = [
                (float(p.X), float(p.Z)) for p in [pl3_p1, pl3_p2, pl3_p3, pl3_p4]
            ]
            new_points += org_points[4:]
            ds.set_headline_coordinates("Stijghoogtelijn 3 (PL3)", new_points)

            result.append(ds)

        return result
