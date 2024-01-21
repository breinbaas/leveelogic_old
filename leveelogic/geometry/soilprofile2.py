from typing import List, Tuple
from matplotlib.pyplot import Figure
from matplotlib.patches import Polygon as MPolygon

from ..models.datamodel import DataModel
from ..geometry.soillayer import SoilLayer
from ..soilinvestigation.cpt import Cpt, CptConversionMethod
from ..geometry.soilprofile1 import SoilProfile1, SoilProfilePlotError
from ..soil.soilcollection import SoilCollection
from .soilpolygon import SoilPolygon


class SoilProfile2(DataModel):
    surface: List[Tuple[float, float]] = []
    x_polder: float = 0.0
    soilprofile_left: SoilProfile1 = None
    soilprofile_right: SoilProfile1 = None
    soilcollection: SoilCollection = None

    @classmethod
    def from_cpts(
        cls,
        surface: List[Tuple[float, float]],
        x_polder: float,
        cpt_left: Cpt,
        cpt_right: Cpt,
        cpt_conversion_method: CptConversionMethod = CptConversionMethod.ROBERTSON,
        minimum_layerheight: float = 0.2,
        peat_friction_ratio: float = 9999,
        fill_material_top: str = "clay",
        fill_material_bottom: str = "sand",
        soilcollection: SoilCollection = SoilCollection(),
    ) -> "SoilProfile2":
        result = SoilProfile2()
        result.surface = surface
        result.x_polder = x_polder
        result.soilcollection = soilcollection

        if result.x_polder <= result.left or result.x_polder >= result.right:
            raise ValueError(f"Invalid x_polder, not inside the limits of the surface.")

        # generate the soillayers from the cpts
        try:
            result.soilprofile_left = cpt_left.to_soilprofile1(
                cptconversionmethod=cpt_conversion_method,
                minimum_layerheight=minimum_layerheight,
                peat_friction_ratio=peat_friction_ratio,
            )
            result.soilprofile_right = cpt_right.to_soilprofile1(
                cptconversionmethod=cpt_conversion_method,
                minimum_layerheight=minimum_layerheight,
                peat_friction_ratio=peat_friction_ratio,
            )
        except Exception as e:
            raise ValueError(f"Got an error converting the cpts to soillayers; {e}")

        surface_top = max([p[1] for p in surface])
        surface_bottom = min([p[1] for p in surface])

        # fill the top and bottom if necessary
        if result.soilprofile_left.top < surface_top:
            result.soilprofile_left.add_top_layer(surface_top, fill_material_top)
        if result.bottom < result.soilprofile_left.bottom:
            result.soilprofile_left.add_bottom_layer(
                surface_bottom, fill_material_bottom
            )
        if result.soilprofile_right.top < surface_top:
            result.soilprofile_right.add_top_layer(surface_top, fill_material_top)
        if result.bottom < result.soilprofile_right.bottom:
            result.soilprofile_right.add_bottom_layer(
                surface_bottom, fill_material_bottom
            )

        # cut out the crosssection
        soilpolygons = result.to_soilpolygons()

        return result

    @property
    def left(self):
        return min([p[0] for p in self.surface])

    @property
    def right(self):
        return max([p[0] for p in self.surface])

    @property
    def top(self):
        return self.soilprofile_left.top

    @property
    def bottom(self):
        return self.soilprofile_left.bottom

    def to_soilpolygons(self) -> List[SoilPolygon]:
        result = [
            SoilPolygon(points=layer.to_points(), soilcode=layer.soilcode)
            for layer in self.soilprofile_left.soillayers
        ]
        result += [
            SoilPolygon(points=layer.to_points(), soilcode=layer.soilcode)
            for layer in self.soilprofile_right.soillayers
        ]
        return result

    def plot(
        self,
        size_x: float = 10,
        size_y: float = 6,
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

        for soillayer in self.soilprofile_left.soillayers:
            try:
                color = self.soilcollection.get(soillayer.soilcode).color
            except Exception as e:
                raise SoilProfilePlotError(
                    f"Could not find a soil definition for soil code '{soillayer.soilcode}'"
                )

            pg = MPolygon(
                [
                    (self.left, soillayer.top),
                    (self.x_polder, soillayer.top),
                    (self.x_polder, soillayer.bottom),
                    (self.left, soillayer.bottom),
                ],
                color=color,
                alpha=0.7,
            )
            ax.add_patch(pg)
            ax.text(self.left, soillayer.bottom, soillayer.soilcode)

        for soillayer in self.soilprofile_right.soillayers:
            try:
                color = self.soilcollection.get(soillayer.soilcode).color
            except Exception as e:
                raise SoilProfilePlotError(
                    f"Could not find a soil definition for soil code '{soillayer.soilcode}'"
                )

            pg = MPolygon(
                [
                    (self.x_polder, soillayer.top),
                    (self.right, soillayer.top),
                    (self.right, soillayer.bottom),
                    (self.x_polder, soillayer.bottom),
                ],
                color=color,
                alpha=0.7,
            )
            ax.add_patch(pg)
            ax.text(self.x_polder, soillayer.bottom, soillayer.soilcode)

        ax.set_xlim(self.left, self.right)
        ax.set_ylim(self.bottom, self.top)

        return fig
