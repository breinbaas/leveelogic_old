from pydantic import BaseModel
from typing import List, Tuple
from shapely import Polygon


class SoilPolygon(BaseModel):
    points: List[Tuple[float, float]] = []
    soilcode: str = ""

    def to_shapely(self) -> Polygon:
        return Polygon(self.points)
