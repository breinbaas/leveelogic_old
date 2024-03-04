from pydantic import BaseModel
from typing import List, Tuple
from shapely import Polygon


class SoilPolygon(BaseModel):
    points: List[Tuple[float, float]] = []
    soilcode: str = ""

    def to_shapely(self) -> Polygon:
        return Polygon(self.points)

    @classmethod
    def from_shapely(cls, polygon: Polygon, soilcode: str) -> "SoilPolygon":
        xx, yy = polygon.exterior.xy
        points = [(p[0], p[1]) for p in zip(xx, yy)]
        return SoilPolygon(points=points, soilcode=soilcode)
