from typing import List, Tuple
from copy import deepcopy
from shapely.geometry import Polygon, MultiPolygon

from .algorithm import Algorithm
from ..dstability import DStability
from ...geometry.soilpolygon import SoilPolygon


class AlgorithmFill(Algorithm):
    """This algorithm will fill the surface of the current geometry until the given line

    Args:
        points (List[Tuple[float, float]]): list of points that form the top boundary of the fill
        soilcode (str): soil code of the fill material
    """

    points: List[Tuple[float, float]]
    soilcode: str

    def _check_input(self):
        if not self.ds.has_soilcode(self.soilcode):
            raise ValueError(
                f"Invalid soilcode '{self.soilcode}', not found in the given model"
            )

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)
        # create a polygon for the crosssection
        polygon_points = self.points
        polygon_points += [
            (self.points[-1][0], self.ds.bottom),
            (self.points[0][0], self.ds.bottom),
        ]
        fill_polygon = Polygon(polygon_points)

        current_polygon = Polygon(self.ds.boundary)

        new_soilpolygons = []  # layers to add
        intersections = fill_polygon.difference(current_polygon)
        if intersections.is_empty:
            pass
        elif type(intersections) == Polygon:
            if intersections.area > 0.01:
                new_soilpolygons.append(
                    SoilPolygon.from_shapely(intersections, self.soilcode)
                )
        elif type(intersections) == MultiPolygon:
            for geom in intersections.geoms:
                if geom.area > 0.01:
                    new_soilpolygons.append(
                        SoilPolygon.from_shapely(geom, self.soilcode)
                    )
        else:
            t = type(intersections)
            raise ValueError("Unhandled intersection type")

        for spg in new_soilpolygons:
            ds.add_layer(spg.points, self.soilcode, label="fill")

        return ds
