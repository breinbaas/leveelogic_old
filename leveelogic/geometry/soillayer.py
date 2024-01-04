from typing import List, Tuple

from ..models.datamodel import DataModel


class SoilLayer(DataModel):
    """Class to store information of a soil layer"""

    top: float
    bottom: float
    soilcode: str

    @property
    def height(self) -> float:
        """Get the height of the soillayer

        Returns:
            float: The height of the soillayer
        """
        return self.top - self.bottom

    @property
    def mid(self) -> float:
        """Get the mid point of the layer

        Returns:
            float: The mid point of the layer
        """
        return (self.top + self.bottom) / 2.0

    def to_points(self, left: float = 0.0, right: float = 0.0) -> List[Tuple]:
        """Convert the soillayer to points of the enclosing polygon

        Args:
            left (float): The left side of the polygon
            right (float): The right side of the polygon

        Returns:
            List[Tuple]: Tuple with topleft, topright, bottom right and bottom left points
        """
        return [
            (left, self.top),
            (right, self.top),
            (right, self.bottom),
            (left, self.bottom),
        ]
