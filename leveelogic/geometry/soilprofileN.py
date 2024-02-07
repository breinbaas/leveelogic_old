from typing import List, Tuple
from copy import deepcopy
from shapely.geometry import Polygon, MultiPolygon
from matplotlib.pyplot import Figure
from matplotlib.patches import Polygon as MPolygon


from ..models.datamodel import DataModel
from .soilprofile1 import SoilProfile1, SoilProfilePlotError
from ..soil.soilcollection import SoilCollection
from .soilpolygon import SoilPolygon


class SoilProfileN(DataModel):
    soilprofiles: List[SoilProfile1] = []
    soilcollection: SoilCollection = SoilCollection()

    @property
    def left(self):
        if len(self.soilprofiles) == 0:
            return 0.0
        return self.soilprofiles[0].left

    @property
    def right(self):
        if len(self.soilprofiles) == 0:
            return 0.0
        return self.soilprofiles[-1].right

    @property
    def top(self):
        if len(self.soilprofiles) == 0:
            return 0.0
        return max([sp.top for sp in self.soilprofiles])

    @property
    def bottom(self):
        if len(self.soilprofiles) == 0:
            return 0.0
        return min([sp.bottom for sp in self.soilprofiles])

    @property
    def soilcodes(self) -> List[str]:
        """Get all the soilcodes that are used in this soilprofileN

        Returns:
            List[str]: a list with all soilcodes used in this soilprofile
        """
        soilcodes = []
        for sp in self.soilprofiles:
            soilcodes += [l.soilcode for l in sp.soillayers]
        return list(set(soilcodes))

    def append(
        self,
        soilprofile1: SoilProfile1,
        fill_material_top: str = "",
        fill_material_bottom: str = "",
    ):
        """Append a new soilprofile1 to the soilprofileN. New soilprofiles will be added to the end (right)
        of the previous soilprofile. In case we already have a soilprofile this means that the left side of the new soil
        profile should match the right side of the previous one.

        If the soilprofile is higher or lower than any of the previous one, top or bottom layers will be
        added with the given material code

        Args:
            soilprofile1 (SoilProfile1): The soilprofile1 to add (to the right side of the current geometry)
            fill_material_top (str, optional): The soilcode for the fillmaterial of top layers. Defaults to "".
            fill_material_bottom (str, optional): The soilcode for the fillmaterial of the bottom layers. Defaults to "".

        Raises:
            ValueError: If any constraints are not met a value error is raised
        """
        if len(self.soilprofiles) == 0:
            self.soilprofiles.append(soilprofile1)
            return

        # check if we match the left side
        if not self.right == soilprofile1.left:
            raise ValueError(
                f"Cannot add the soilprofile since the left side ({soilprofile1.left}) does not correspond with the right side ({self.right}) of the last soilprofile in this soilprofileN"
            )

        # check if we need to adjust the top and bottom of the soilprofiles
        if soilprofile1.top > self.top:
            for i, sp in enumerate(self.soilprofiles):
                if sp.top < soilprofile1.top:
                    if fill_material_top == "":
                        raise ValueError(
                            "Adding a soilprofile with a top which is higher than the others so we need a fill_material_top"
                        )
                    self.soilprofiles[i].add_top_layer(
                        soilprofile1.top, fill_material_top
                    )
        elif soilprofile1.top < self.top:
            if fill_material_top == "":
                raise ValueError(
                    "Adding a soilprofile with a top that is lower than the others so we need a fill_material_top"
                )
            soilprofile1.add_top_layer(self.top, fill_material_top)

        if soilprofile1.bottom < self.bottom:
            for i, sp in enumerate(self.soilprofiles):
                if soilprofile1.bottom < sp.bottom:
                    if fill_material_bottom == "":
                        raise ValueError(
                            "Adding a soilprofile with a bottom which is lower than the others so we need a fill_material_bottom"
                        )
                    self.soilprofiles[i].add_bottom_layer(
                        soilprofile1.bottom, fill_material_bottom
                    )
        elif self.bottom < soilprofile1.bottom:
            if fill_material_bottom == "":
                raise ValueError(
                    "Adding a soilprofile with a bottom which is higher than the others so we need a fill_material_bottom"
                )
            soilprofile1.add_bottom_layer(self.bottom, fill_material_top)

        self.soilprofiles.append(soilprofile1)

    def to_soilpolygons(
        self,
        crosssection_points: List[Tuple[float, float]] = [],
        fill_material_top: str = "",
        fill_material_bottom: str = "",
    ):
        # CHECKS
        # check the soilcodes
        soilcodes = self.soilcodes
        if fill_material_bottom != "":
            soilcodes.append(fill_material_bottom)
        if fill_material_top != "":
            soilcodes.append(fill_material_top)

        missing_soilcodes = []
        for sc in soilcodes:
            if not self.soilcollection.has_soilcode(sc):
                missing_soilcodes.append(sc)
        if len(missing_soilcodes) > 0:
            raise ValueError(
                f"The soilcollections misses the soilcodes for {','.join(missing_soilcodes)}"
            )

        # if we have a crosssection every soilprofile1 needs to extend to the top and bottom of the crosssection
        if len(crosssection_points) != 0:
            crs_top = max([p[1] for p in crosssection_points])
            crs_bottom = min([p[1] for p in crosssection_points])

            for sp1 in self.soilprofiles:
                if sp1.top < crs_top and fill_material_top == "":
                    raise ValueError(
                        f"The top of the crosssection ({crs_top}) is higher than some of the soilprofiles, a soilcode_fill_material_top should be given"
                    )
                if crs_bottom < sp1.bottom and fill_material_bottom == "":
                    raise ValueError(
                        f"The bottom of the crosssection ({crs_bottom}) is lower than some of the soilprofiles, a soilcode_fill_material_bottom should be given"
                    )

        # EXECUTION
        soilpolygons = []
        if len(crosssection_points) == 0:
            for sp1 in self.soilprofiles:
                soilpolygons += sp1.to_soilpolygons()
            return soilpolygons

        # this one adds the crosssection which is more complicated
        # first make sure to add top and bottom fill material if necessary
        cp = deepcopy(self)  # we don't want to work on the original soilprofiles
        for i, sp1 in enumerate(cp.soilprofiles):
            if sp1.top < crs_top:
                cp.soilprofiles[i].add_top_layer(crs_top, fill_material_top)
            if crs_bottom < sp1.bottom:
                cp.soilprofiles[i].add_bottom_layer(crs_bottom, fill_material_bottom)

        # convert to soilpolygons
        soilpoygons = []
        for sp in cp.soilprofiles:
            soilpolygons += sp.to_soilpolygons()

        # create a polygon for the crosssection
        top_polygon_points = [
            (self.left, cp.top + 1.0),
            (self.right, cp.top + 1.0),
        ]
        top_polygon_points += crosssection_points[::-1]
        top_polygon = Polygon(top_polygon_points)

        # cut it out of the current soillayers
        final_soilpolygons = []
        for spg in soilpolygons:
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
        return final_soilpolygons

    def plot(
        self,
        size_x: float = 10,
        size_y: float = 6,
    ) -> Figure:
        """Plot the soilprofileN to a Figure

        Args:
            size_x (float): figure width in inches, default 8
            size_y (float): figure height in inches, default 12


        Returns:
            plot (Figure): the matplotlib figure
        """

        fig = Figure(figsize=(size_x, size_y))
        ax = fig.add_subplot()

        for sp in self.soilprofiles:
            for soillayer in sp.soillayers:
                try:
                    color = self.soilcollection.get(soillayer.soilcode).color
                except Exception as e:
                    raise SoilProfilePlotError(
                        f"Could not find a soil definition for soil code '{soillayer.soilcode}'"
                    )

                pg = MPolygon(
                    [
                        (sp.left, soillayer.top),
                        (sp.right, soillayer.top),
                        (sp.right, soillayer.bottom),
                        (sp.left, soillayer.bottom),
                    ],
                    color=color,
                    alpha=0.7,
                )
                ax.add_patch(pg)
                ax.text(sp.left, soillayer.bottom, soillayer.soilcode)

        ax.set_xlim(self.left, self.right)
        ax.set_ylim(self.bottom, self.top)

        return fig
