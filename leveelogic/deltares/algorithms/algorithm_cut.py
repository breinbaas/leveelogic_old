from typing import List, Tuple
from copy import deepcopy
from shapely.geometry import Polygon, MultiPolygon

from .algorithm import Algorithm
from ..dstability import DStability
from ...geometry.soilpolygon import SoilPolygon


class AlgorithmCut(Algorithm):
    """This algorithm will cut out the given polygon from the current geometry

    WARNING; You will lose information from the original calculation. This algorithm
    will ONLY save the layers.

    Args:
        points (List[Tuple[float, float]]): list of points that form the lower boundary of the cut
    """

    points: List[Tuple[float, float]]

    def _check_input(self):
        pass

    def _execute(self) -> DStability:
        # create a polygon for the crosssection
        top_polygon_points = [
            (self.ds.left, self.ds.top + 1.0),
            (self.ds.right, self.ds.top + 1.0),
        ]
        top_polygon_points += self.points[::-1]
        top_polygon = Polygon(top_polygon_points)

        # cut it out of the current soillayers
        final_soilpolygons = []
        for spg in self.ds.soilpolygons:
            layer_polygon = Polygon(spg.points)
            intersections = layer_polygon.difference(top_polygon)

            if intersections.is_empty:
                continue
            elif type(intersections) == Polygon:
                final_soilpolygons.append(
                    SoilPolygon.from_shapely(intersections, spg.soilcode)
                )
            elif type(intersections) == MultiPolygon:
                for geom in intersections.geoms:
                    final_soilpolygons.append(
                        SoilPolygon.from_shapely(geom, spg.soilcode)
                    )
            else:
                t = type(intersections)
                raise ValueError("Unhandled intersection type")

        # return the final result
        ds = DStability.from_soilpolygons(
            final_soilpolygons, self.ds.soilcollection, old_ds=self.ds
        )
        return ds
