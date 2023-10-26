from typing import List, Dict, Optional
import numpy as np
from matplotlib.pyplot import Figure
from matplotlib.patches import Polygon
from pydantic import BaseModel
from copy import deepcopy

from ..geometry.soillayer import SoilLayer
from ..models.datamodel import DataModel
from ..soil.soilcollection import SoilCollection


class SoilProfile1GapError(Exception):
    """This exception is raised if there is a gap between two consequetive soillayers"""

    pass


class SoilProfile1HeightError(Exception):
    """This exception is raised if there is a negative height in a soillayer"""

    pass


class SoilProfilePlotError(Exception):
    """This exception is raised if an error like an unknown soiltype was found during plotting"""

    pass


class SoilProfile1(DataModel):
    """one dimensional stack of soillayers"""

    lat: float = 0.0
    lon: float = 0.0
    soillayers: List[SoilLayer] = []

    @property
    def top(self) -> float:
        """Returns the top of the soilprofile

        Returns:
            float: Top of the soilprofile
        """
        if len(self.soillayers) > 0:
            return self.soillayers[0].top
        else:
            return np.nan

    @property
    def bottom(self) -> float:
        """Returns the bottom of the soilprofile

        Returns:
            float: Bottom of the soilprofile
        """
        if len(self.soillayers) > 0:
            return self.soillayers[-1].bottom
        else:
            return np.nan

    @property
    def height(self) -> float:
        """Returns the height of the soilprofile

        Returns:
            float: Height of the soilprofile
        """
        return round(self.top - self.bottom, 2)

    def _merge(self):
        """Merge the soillayers if two consecutive soillayers are of the same type"""
        result = []
        for i in range(len(self.soillayers)):
            if i == 0:
                result.append(self.soillayers[i])
            else:
                if self.soillayers[i].soilcode == result[-1].soilcode:
                    result[-1].bottom = self.soillayers[i].bottom
                else:
                    result.append(self.soillayers[i])
        self.soillayers = result

        # """
        # """
        # """Apply a minimal height to the soillayers, layers that are too thin will be spread out
        # over the adjacent soillayers"""

    def apply_minimum_height(self, minimum_height=0.1):
        """Apply a minimum height to the soillayers,  layers that are too thin will be spread out  over the adjacent soillayers

        Args:
            minimum_height (float, optional): Minimum layer height. Defaults to 0.1m.

        Raises:
            SoilProfile1HeightError: Returns an error if the geometry is invalid
        """

        if self.height < minimum_height:
            raise SoilProfile1HeightError(
                f"Trying to apply a minimum height of {minimum_height}m to a borehole that is {self.height}m high"
            )

        if len([s for s in self.soillayers if s.height < minimum_height]) == 0:
            return

        for i in range(len(self.soillayers)):
            if self.soillayers[i].height < minimum_height:
                if i == 0:
                    self.soillayers[1].top = self.soillayers[0].top
                    self.soillayers.remove(self.soillayers[0])
                    break
                elif i == len(self.soillayers) - 1:
                    self.soillayers[-2].bottom = self.soillayers[-1].bottom
                    self.soillayers.remove(self.soillayers[-1])
                    break
                else:
                    zmid = round(
                        (self.soillayers[i].top + self.soillayers[i].bottom) / 2.0, 2
                    )
                    self.soillayers[i - 1].bottom = zmid
                    self.soillayers[i + 1].top = zmid
                    self.soillayers.remove(self.soillayers[i])
                    break
        self.apply_minimum_height(minimum_height)  # recursive

    def validate(self):
        """Will raise an exception if an error is found in the geometry"""
        succes = True
        # layers top is higher than bottom and not 0
        for sl in self.soillayers:
            if sl.height <= 0:
                raise SoilProfile1HeightError(
                    f"Negvative soillayer height in layer {sl.soilcode} found"
                )

        # layers do not have gaps
        for i in range(1, len(self.soillayers)):
            if self.soillayers[i - 1].bottom != self.soillayers[i].top:
                raise SoilProfile1GapError(f"Gap found between layers {i-1} and {i}")
