from copy import deepcopy
from geolib.geometry import Point
from math import floor
from dotenv import load_dotenv
import os
from pathlib import Path
import math

from ..dstability import DStability
from .algorithm import Algorithm
from ...helpers import polyline_polyline_intersections
from ...geometry.characteristic_point import CharacteristicPointType

load_dotenv()

MAX_ITERATIONS = 10


class AlgorithmBermFromZ(Algorithm):
    soilcode: str
    required_sf: float = 1.0
    x_base: float
    angle: float = 30
    initial_height: float
    slope_top: float
    slope_side: float
    step_size: float = 0.25

    def _check_input(self):
        # do we have this soilcode
        if not self.ds.has_soilcode(self.soilcode):
            raise ValueError(f"AlgorithmBerm got an invalid soilcode '{self.soilcode}'")

        # is the temp file path set?
        try:
            _ = os.getenv("TEMP_FILES_PATH")
        except Exception as e:
            raise ValueError(
                f"The temp files path is not set in the environment file. 'TEMP_FILES_PATH=...'"
            )

    def _execute(self) -> DStability:
        temp_files_path = os.getenv("TEMP_FILES_PATH")

        sf = 0.0
        iter = 0.0
        h = self.initial_height

        while sf < self.required_sf:
            ds = deepcopy(self.ds)

            p1 = (self.x_base, self.ds.z_at(self.x_base)[0])
            p2 = (p1[0], p1[1] + h)
            p3 = (
                self.ds.right,
                p1[1] + math.sin(math.radians(self.angle)) * (self.ds.right - p1[0]),
            )
            p4 = (self.ds.right, p2[1] - (self.ds.right - p2[0]) / self.slope_top)
            p5 = polyline_polyline_intersections([p2, p4], [p1, p3])[0]
            p6 = (self.ds.right, p5[1] - (self.ds.right - p5[0]) / self.slope_side)
            intersections = polyline_polyline_intersections(self.ds.surface, [p5, p6])[
                0
            ]
            p7 = (intersections[0], self.ds.z_at(intersections[0])[0])
            p8 = (self.ds.left, p2[1] + (p2[0] - self.ds.left) / self.slope_top)

            intersections = polyline_polyline_intersections(self.ds.surface, [p2, p8])[
                -1
            ]
            p9 = (intersections[0], self.ds.z_at(intersections[0])[0])

            new_layer_points = [Point(x=p[0], z=p[1]) for p in [p9, p5, p7]]

            new_layer_points += [
                Point(x=p[0], z=p[1])
                for p in self.ds.surface_points_between(p9[0], p7[0])[::-1]
            ]
            new_layer_points.append(Point(x=p1[0], z=p1[1]))
            ds.model.add_layer(new_layer_points, self.soilcode)
            ds.serialize(Path(temp_files_path) / f"berm_{h}.stix")

            try:
                ds.model.execute()
                sf = ds.model.get_result(0, 0).FactorOfSafety
            except:
                raise ValueError(
                    "Could not find a valid solution with these parameters."
                )

            if sf > self.required_sf:
                return ds

            h += self.step_size

            if iter == MAX_ITERATIONS:
                raise ValueError(
                    f"Could not converge to a solution in {MAX_ITERATIONS} steps for the given safety factor."
                )
            else:
                iter += 1
