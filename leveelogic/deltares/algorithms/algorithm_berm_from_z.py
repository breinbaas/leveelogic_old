from copy import deepcopy
from geolib.geometry import Point
from math import floor
from dotenv import load_dotenv
import os
from pathlib import Path
import math
import numpy as np

from ..dstability import DStability
from .algorithm import Algorithm
from ...helpers import polyline_polyline_intersections
from ...geometry.characteristic_point import CharacteristicPointType
from ..runner import Runner

# DEBUG
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Polygon

load_dotenv()

MAX_ITERATIONS = 100


class AlgorithmBermFromZ(Algorithm):
    soilcode: str
    required_sf: float = 1.0
    x_base: float
    angle: float = 30
    initial_height: float
    slope_top: float
    slope_side: float
    step_size: float = 0.25
    save_files: bool = False

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
        runner = Runner()

        sf = 0.0
        iter = 0.0
        h = self.initial_height

        # we make 6 calculations to run parallel
        for h in np.arange(
            self.initial_height,
            self.initial_height + 6.1 * self.step_size,
            self.step_size,
        ):
            # while sf < self.required_sf:
            ds = deepcopy(self.ds)

            p1 = (self.x_base, self.ds.z_at(self.x_base)[0])
            p2 = (p1[0], p1[1] + h)
            p3 = (
                self.ds.right,
                p1[1] + math.sin(math.radians(self.angle)) * (self.ds.right - p1[0]),
            )
            p4 = (self.ds.right, p2[1] - (self.ds.right - p2[0]) / self.slope_top)

            # this can only lead to one intersection unless slope top == angle
            p5 = polyline_polyline_intersections([p2, p4], [p1, p3])[0]

            # we need the last intersection with the surface for our berm line
            p6 = (self.ds.right, p5[1] - (self.ds.right - p5[0]) / self.slope_side)
            intersections = polyline_polyline_intersections(self.ds.surface, [p5, p6])[
                -1
            ]
            p7 = (intersections[0], self.ds.z_at(intersections[0])[0])

            p8 = (self.ds.left, p2[1] + (p2[0] - self.ds.left) / self.slope_top)
            # we need the first point left of p2 on our surface to complete our berm line
            intersections = polyline_polyline_intersections(self.ds.surface, [p2, p8])[
                -1
            ]
            p9 = (intersections[0], self.ds.z_at(intersections[0])[0])

            # now we have the berm but this line can intersect multiple parts of the geometry (in case of for example the spikey geometry)
            # get all the intersections of the surface with the berm line
            # we add p9 as the first point
            berm_intersections = [p9] + polyline_polyline_intersections(
                [p9, p5, p6], self.ds.surface
            )

            for i in range(0, len(berm_intersections), 2):
                tp1 = list(berm_intersections[i])
                tp2 = list(berm_intersections[i + 1])
                tp1[1] = ds.z_at(tp1[0])[0]
                tp2[1] = ds.z_at(tp2[0])[0]

                new_points = [tp1]
                if tp1[0] < p5[0] and p5[0] < tp2[0]:
                    new_points.append(p5)
                new_points.append(tp2)
                new_points += self.ds.surface_points_between(tp1[0], tp2[0])[::-1]

                new_layer_points = [Point(x=p[0], z=p[1]) for p in new_points]
                ds.model.add_layer(new_layer_points, self.soilcode)

            # debug plot
            # fig = Figure(figsize=(20, 10))
            # ax = fig.add_subplot()
            # for sl in ds.soillayers:
            #     pg = Polygon(
            #         sl["points"],
            #         facecolor="none",
            #         edgecolor="black",
            #         lw=0.7,
            #     )
            #     ax.add_patch(pg)
            # points = [p1, p2, p3, p4, p5, p6, p7, p8, p9]
            # ax.scatter([p[0] for p in points], [p[1] for p in points])
            # ax.plot([p9[0], p5[0], p7[0]], [p9[1], p5[1], p7[1]], "k--")

            # ax.set_xlim(p9[0] - 5.0, p7[0] + 5.0)
            # ax.set_ylim(ds.bottom, ds.top)

            # fig.savefig("tests/testdata/output/berm_debug_plot.png")

            # new_layer_points += [
            #     Point(x=p[0], z=p[1])
            #     for p in self.ds.surface_points_between(p9[0], p7[0])[::-1]
            # ]

            fname = Path(temp_files_path) / f"berm_{h:.2f}.stix"
            ds.serialize(fname)

            runner.models.append(ds)

            # try:
            #     ds.model.execute()
            #     sf = ds.model.get_result(0, 0).FactorOfSafety

            #     # might be useful for debugging or other purposes
            #     if not self.save_files:
            #         file_path = Path(fname)
            #         file_path.unlink()
            # except:
            #     raise ValueError(
            #         "Could not find a valid solution with these parameters."
            #     )

            # if sf > self.required_sf:
            #     return ds

            h += self.step_size

            if iter == MAX_ITERATIONS:
                raise ValueError(
                    f"Could not converge to a solution in {MAX_ITERATIONS} steps for the given safety factor."
                )
            else:
                iter += 1

        runner.execute()
        i = 1
