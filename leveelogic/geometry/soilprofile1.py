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
    left: int = 0
    right: int = 0
    soillayers: List[SoilLayer] = []

    @property
    def mid(self) -> float:
        return (self.left + self.right) / 2.0

    @property
    def top(self) -> float:
        if len(self.soillayers) > 0:
            return self.soillayers[0].top
        else:
            return np.nan

    @property
    def bottom(self) -> float:
        if len(self.soillayers) > 0:
            return self.soillayers[-1].bottom
        else:
            return np.nan

    @property
    def height(self) -> float:
        return round(self.top - self.bottom, 2)

    @classmethod
    def from_short_string(cls, s) -> "SoilProfile1":
        """Generate a soilprofile1 from the given short string


        Args:
            s (str): a string with the following format; top1,bottom1,soilcode1,bottom2,soilcode2 etc

        Returns:
            SoilProfile1: None if invalid or else the SoilProfile1
        """
        try:
            args = s.split(",")
            tops = [float(args[0])]
            bots = [float(args[i]) for i in range(1, len(args), 2)]
            tops += bots[:-1]
            soilcodes = [args[i].strip() for i in range(2, len(args), 2)]

            sp1 = SoilProfile1()
            for i in range(len(soilcodes)):
                sp1.soillayers.append(
                    SoilLayer(top=tops[i], bottom=bots[i], soilcode=soilcodes[i])
                )

            return sp1

        except Exception as e:
            return None

    def to_short_string(self) -> str:
        """Return the soillayers as a string with minimal information for example
        2,0,peat,-2,clay.. which means;
        from 2 to 0 peat
        from 0 to -2 clay
        etc..

        Returns:
            str: empty string for no layers or str like top,bottom,layer1,bottom,layer2 etc.
        """
        if len(self.soillayers) == 0:
            return ""

        result = f"{self.soillayers[0].top},{self.soillayers[0].bottom},{self.soillayers[0].soilcode}"
        for sl in self.soillayers[1:]:
            result += f",{sl.bottom},{sl.soilcode}"

        return result

    def rename(self, new_soilnames: Dict):
        """Rename the soillayers in the soilprofile using the given dictionary

        Args:
            new_soilnames (Dict): A dictionary with current name : new name value pairs
        """
        for sl in self.soillayers:
            if sl.soilcode in new_soilnames:
                sl.soilcode = new_soilnames[sl.soilcode]
        self._merge()

    def soilcode_at_z(self, z: float) -> str:
        """Get the soilcode at the given z coordinate in the soilprofile

        Args:
            z (float): The depth at which to get the soilcode

        Returns:
            str: The soilcode of the soillayer at the given z or empty string if none
        """
        for sl in self.soillayers:
            if sl.bottom <= z and z <= sl.top:
                return sl.soilcode
        return ""

    def add_soilprofile1(self, soilprofile1: "SoilProfile1"):
        """Add a soilprofile to the existing soil profile. Existing soillayers will be replaced if they overlap.
        Will raise a SoilProfile1GapError if gaps are found

        Args:
            soilprofile1 (SoilProfile1): Soilprofile to add to the existing soil profile
        """
        if soilprofile1.bottom > self.top:
            raise SoilProfile1GapError(
                f"The bottom of the new soilprofile {soilprofile1.bottom} is higher than the top of current soilprofile {self.top}"
            )

        if soilprofile1.top < self.bottom:
            raise SoilProfile1GapError(
                f"The top of the new soilprofile {soilprofile1.top} is lower than the top of current soilprofile {self.bottom}"
            )

        for sl in soilprofile1.soillayers:
            self._insert(
                sl, check=False
            )  # the first layers might be above the top of our current soilprofile and we don't want an error for that

    def _insert(self, new_soillayer: SoilLayer, check=True):
        """Insert a soillayer into the current soillayers

        Args:
            new_soillayer (SoilLayer): The soillayer to insert
            check (bool): check if the soillayer lies in the current constraints, if True
            a GapError might be raised if the soillayer is higher than the bottom of the
            current soilprofile or lower than the top of the current soilprofile.
        """
        if check and new_soillayer.bottom > self.top:
            raise SoilProfile1GapError(
                f"The bottom of the new soillayer {new_soillayer.bottom} is higher than the top of current soilprofile {self.top}"
            )

        if check and new_soillayer.top < self.bottom:
            raise SoilProfile1GapError(
                f"The top of the new soillayer {new_soillayer.top} is lower than the top of current soilprofile {self.bottom}"
            )

        newlayers = sorted(
            self.soillayers + [new_soillayer],
            key=lambda x: (x.top, x.bottom),
            reverse=True,
        )
        idx = newlayers.index(new_soillayer)
        for i in range(0, idx):
            if newlayers[i].top < new_soillayer.top:
                newlayers[i].top = new_soillayer.top
            if newlayers[i].bottom < new_soillayer.top:
                newlayers[i].bottom = new_soillayer.top

        for i in range(idx + 1, len(newlayers)):
            if newlayers[i].top > new_soillayer.bottom:
                newlayers[i].top = new_soillayer.bottom
            if newlayers[i].bottom > new_soillayer.bottom:
                newlayers[i].bottom = new_soillayer.bottom

        # remove layers with negative or zero height
        self.soillayers = [layer for layer in newlayers if layer.height > 0]
        self._merge()

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

    def apply_minimum_height(self, minimum_height=0.1):
        """Apply a minimal height to the soillayers, layers that are too thin will be spread out
        over the adjacent soillayers"""
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

    def add_top_layer(self, top: float, soilcode: str):
        """Add a layer on top of the current soillayers with a given top coordinate and the given soilcode

        Args:
            top (float): top of the new layer that will be placed on top of the current ones
            soilcode (str): soilcode of the new top layer
        """
        if len(self.soillayers) == 0:
            raise SoilProfile1HeightError(
                f"Trying to add a top soillayer but the soilprofile is empty."
            )
        if top <= self.soillayers[0].top:
            raise SoilProfile1HeightError(
                f"Trying to add a top soillayer but the top is lower than or equal to the current soilprofile."
            )

        # finally.. add it!
        self.soillayers.insert(
            0, SoilLayer(top=top, bottom=self.soillayers[0].top, soilcode=soilcode)
        )

    def cut(
        self, top: float, bottom: float, inline: bool = False
    ) -> Optional["SoilProfile1"]:
        """Create a copy of the Soilprofile but cut at the given depths

        Args:
            top (float): top boundary of the soilprofile
            bottom (float): bottom boundary of the soilprofile
            inline (bool): apply to self (True) or return a new Soilprofile (False)


        Returns:
            Soilprofile: copy of the soilprofile but cut at the given limits
        """
        newsoillayers = []

        for layer in self.soillayers:
            t, b = -1e9, 1e9
            if layer.top > bottom:
                t = min(layer.top, top)
            if layer.bottom < top:
                b = max(layer.bottom, bottom)

            if t > b:
                newsoillayers.append(
                    SoilLayer(top=t, bottom=b, soilcode=layer.soilcode)
                )

        if len(newsoillayers) == 0:
            raise ValueError(
                f"The given top and bottom parameters result in an empty soilprofile."
            )

        if inline:
            self.soillayers = newsoillayers
        else:
            result = deepcopy(self)
            result.soillayers = newsoillayers
            return result

    def add_bottom_layer(self, bottom: float, soilcode: str):
        """Add a layer on the bottom of the current soillayers with the given bottom coordinate and the given soilcode

        Args:
            bottom (float): the bottom of the new layer
            soilcode (str): the soilcode of the new layer
        """
        if len(self.soillayers) == 0:
            raise SoilProfile1HeightError(
                f"Trying to add a bottom soillayer but the soilprofile is empty."
            )
        if bottom >= self.soillayers[-1].bottom:
            raise SoilProfile1HeightError(
                f"Trying to add a bottom soillayer but the bottom is higher than or equal to the current soilprofile."
            )

        self.soillayers.append(
            SoilLayer(top=self.soillayers[-1].bottom, bottom=bottom, soilcode=soilcode)
        )

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

    def plot(
        self,
        size_x: float = 3,
        size_y: float = 6,
        soilcollection: SoilCollection = SoilCollection(),
    ) -> Figure:
        """Plot the borehole to a Figure

        Args:
            size_x (float): figure width in inches, default 8
            size_y (float): figure height in inches, default 12


        Returns:
            plot (Figure): the matplotlib figure
        """

        fig = Figure(figsize=(size_x, size_y))
        ax = fig.add_subplot()

        for soillayer in self.soillayers:
            try:
                color = soilcollection.get(soillayer.soilcode).color
            except Exception as e:
                raise SoilProfilePlotError(
                    f"Could not find a soil definition for soil code '{soillayer.soilcode}'"
                )

            pg = Polygon(
                [
                    (0.1, soillayer.top),
                    (0.9, soillayer.top),
                    (0.9, soillayer.bottom),
                    (0.1, soillayer.bottom),
                ],
                color=color,
                alpha=0.7,
            )
            ax.add_patch(pg)
            ax.text(0.11, soillayer.bottom, soillayer.soilcode)

        ax.set_ylim(self.bottom, self.top)

        return fig
