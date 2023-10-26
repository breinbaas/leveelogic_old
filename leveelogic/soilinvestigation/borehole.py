from pydantic import BaseModel
from typing import List, Union, Optional
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
from matplotlib.pyplot import Figure
from copy import deepcopy

from .gefxmlreader import XmlBorehole
from ..geometry.soillayer import SoilLayer
from ..helpers import xy_to_latlon, soilcode_to_parameters
from ..geometry.soilprofile1 import SoilProfile1

GEF_COLUMN_TOP = 1
GEF_COLUMN_BOTTOM = 2


class BoreholeReadError(Exception):
    """This exception is raised if the passed borehole data is invalid"""

    pass


class BoreholeDataError(Exception):
    """This exception is raised if invalid borehole data is found after reading the borehole"""

    pass


class Borehole(BaseModel):
    x: float = 0.0
    y: float = 0.0
    xy: Union[float, float] = (0, 0)
    latlon: Union[float, float] = (0, 0)
    top: float = 0.0
    bottom: float = 0.0

    soillayers: List[SoilLayer] = []

    name: str = ""
    filedate: str = ""
    startdate: str = ""
    filename: str = ""

    @classmethod
    def from_file(self, filename: str) -> "Borehole":
        try:
            data = open(filename, "r", encoding="utf-8", errors="ignore").read()
            return Borehole.from_string(data, Path(filename).suffix.lower())
        except Exception as e:
            raise BoreholeReadError(
                f"Error reading borehole file '{filename}', got error '{e}' "
            )

    @classmethod
    def from_string(self, data: str, suffix: str) -> Optional["Borehole"]:
        borehole = Borehole()
        if suffix == ".xml":
            try:
                borehole.read_xml(data)
                return borehole
            except Exception as e:
                raise BoreholeReadError(f"Error reading XmlBore data; '{e}'")
        elif suffix == ".gef":
            try:
                borehole.read_gef(data)
                return borehole
            except Exception as e:
                raise BoreholeReadError(f"Error reading GEFBore data; '{e}'")
        else:
            raise BoreholeReadError(
                f"Invalir or unsupported filetype '{suffix}', supported are *.gef, *.xml"
            )

    def _post_process(self):
        if len(self.soillayers) > 0:
            self.bottom = self.soillayers[-1].bottom
        self.latlon = xy_to_latlon(self.x, self.y)
        self.xy = (self.x, self.y)

    def read_gef(self, data: str):
        reading_header = True
        metadata = {
            "record_seperator": "",
            "column_seperator": " ",
            "columninfo": {},
            "last_column": 2,
        }
        for line in data.split("\n"):
            if reading_header:
                if line.find("#EOH") >= 0:
                    reading_header = False
                else:
                    self._parse_header_line(line, metadata)
            else:
                self._parse_data_line(line, metadata)

        self._post_process()

    def compress(self, agressive: bool = False):
        """Compress the soillayers based on their names. You can compress
        normaly which will merge soillayers with the same soilcode or you can
        compress agressively where only the first part of the soilcode will
        be used as the name - example;

         0.0;-1.0;Vks1_Clayey
        -1.0;-1.2;Vks1_Clayey
        -1.2;-1.5;Vks1_Very_Clayey
        -1.5;-2.0;Vks1_Clayey
        -2.0;-3.0;Clay
        ..

        normal compression will result in;
         0.0;-1.2;Vks1_Clayey
        -1.2;-1.5;Vks1_Very_Clayey
        -1.5;-2.0;Vks1_Clayey
        -2.0;-3.0;Clay

        agressive compression will result in;
         0.0;-2.0;Vks1
        -2.0;-3.0;Clay
        ..

        Args:
            agressive (bool, optional): Agressive will only check the first part of the name. Defaults to False.
        """
        if agressive:
            new_soillayers = []
            for sl in self.soillayers:
                args = sl.soilcode.split("_")
                if len(args) > 0:
                    new_soillayers.append(
                        SoilLayer(top=sl.top, bottom=sl.bottom, soilcode=args[0])
                    )
                else:
                    new_soillayers.append(sl)
            self.soillayers = new_soillayers

        self._merge_layers()

    def read_xml(self, data: str):
        xmlbore = XmlBorehole()
        xmlbore.parse_xml_string(data)

        # now convert to pygef Cpt class and use that logic to read it
        self.read_gef(xmlbore.to_gef_string())

    @property
    def length(self) -> float:
        return self.top - self.bottom

    @property
    def lat(self) -> float:
        return self.latlon[0]

    @property
    def lon(self) -> float:
        return self.latlon[1]

    @property
    def date(self) -> str:
        """Return the date of the borehole in the following order (if available) startdate, filedata, empty string (no date)

        Args:
            None

        Returns:
            str: date in format YYYYMMDD"""
        if self.startdate != "":
            return self.startdate
        elif self.filedate != "":
            return self.filedate
        else:
            raise ValueError("This geffile has no date or invalid date information.")

    def _parse_header_line(self, line: str, metadata: dict) -> None:
        try:
            keyword, argline = line.split("=")
        except Exception as e:
            raise ValueError(f"Error reading headerline '{line}' -> error {e}")

        keyword = keyword.strip().replace("#", "")
        argline = argline.strip()
        args = argline.split(",")

        if keyword in ["PROCEDURECODE", "REPORTCODE"]:
            if args[0].upper().find("CPT") > -1:
                raise BoreholeReadError("This is a cpt file instead of a Borehole file")
        elif keyword == "RECORDSEPARATOR":
            metadata["record_seperator"] = args[0]
        elif keyword == "COLUMN":
            metadata["last_column"] = int(args[0])
        elif keyword == "COLUMNSEPARATOR":
            metadata["column_seperator"] = args[0]
        elif keyword == "COLUMNINFO":
            try:
                column = int(args[0])
                dtype = int(args[3].strip())
                metadata["columninfo"][dtype] = column - 1
            except Exception as e:
                raise ValueError(f"Error reading columninfo '{line}' -> error {e}")
        elif keyword == "XYID":
            try:
                self.x = round(float(args[1].strip()), 2)
                self.y = round(float(args[2].strip()), 2)
            except Exception as e:
                raise ValueError(f"Error reading xyid '{line}' -> error {e}")
        elif keyword == "ZID":
            try:
                self.top = float(args[1].strip())
            except Exception as e:
                raise ValueError(f"Error reading zid '{line}' -> error {e}")
        elif keyword == "TESTID":
            self.name = args[0].strip()
        elif keyword == "FILEDATE":
            try:
                yyyy = int(args[0].strip())
                mm = int(args[1].strip())
                dd = int(args[2].strip())

                if yyyy < 1900 or yyyy > 2100 or mm < 1 or mm > 12 or dd < 1 or dd > 31:
                    raise ValueError(f"Invalid date {yyyy}-{mm}-{dd}")

                self.filedate = f"{yyyy}{mm:02}{dd:02}"
            except:
                self.filedate = ""
        elif keyword == "STARTDATE":
            try:
                yyyy = int(args[0].strip())
                mm = int(args[1].strip())
                dd = int(args[2].strip())
                self.startdate = f"{yyyy}{mm:02}{dd:02}"
                if yyyy < 1900 or yyyy > 2100 or mm < 1 or mm > 12 or dd < 1 or dd > 31:
                    raise ValueError(f"Invalid date {yyyy}-{mm}-{dd}")
            except:
                self.startdate = ""

    def _parse_data_line(self, line: str, metadata: dict) -> None:
        try:
            if len(line.strip()) == 0:
                return
            args = line.strip().split(metadata["column_seperator"])
            args = [
                arg.strip()
                for arg in args
                if len(arg.strip()) > 0 and arg.strip() != metadata["record_seperator"]
            ]

            z_top_column = metadata["columninfo"][GEF_COLUMN_TOP]
            z_bottom_column = metadata["columninfo"][GEF_COLUMN_BOTTOM]
            soilcode_start_column = metadata["last_column"]

            z_top = float(args[z_top_column])
            z_bottom = float(args[z_bottom_column])

            if (
                z_bottom > z_top
            ):  # sometimes people use positive depth values from z_top in the GEF file.. annoying..
                z_top = self.top - z_top
                z_bottom = self.top - z_bottom

            # no columninfo for the text of the sample, expect all after column GEF_COLUMN_BOTTOM
            soilcode = (
                "_".join(args[soilcode_start_column:]).replace('"', "").replace("'", "")
            )
            soilcode = soilcode.replace(" ", "_")

            self.soillayers.append(
                SoilLayer(
                    bottom=round(z_bottom, 2),
                    top=round(z_top, 2),
                    soilcode=soilcode,
                )
            )
        except Exception as e:
            raise ValueError(f"Error reading dataline '{line}' -> error {e}")

    def _merge_layers(self) -> None:
        """Merge consecutive layers if they have the same soil code

        Args:
            None

        Returns:
            None
        """
        # merge layers with same name
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

    def cut(
        self, top: float, bottom: float, inline: bool = False
    ) -> Optional["Borehole"]:
        """Create a copy of the Borehole but cut at the given depths

        Args:
            top (float): top boundary of the borehole
            bottom (float): bottom boundary of the borehole

        Returns:
            Borehole: copy of the borehole but cut at the given limits
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
                f"The given top and bottom parameters result in an empty borehole."
            )

        if inline:
            self.soillayers = newsoillayers
            self.top = newsoillayers[0].top
            self.bottom = newsoillayers[-1].bottom
        else:
            result = deepcopy(self)
            result.soillayers = newsoillayers
            result.top = newsoillayers[0].top
            result.bottom = newsoillayers[-1].bottom
            return result

    def to_soilprofile1(self):
        return SoilProfile1(
            lat=self.latlon[0],
            lon=self.latlon[1],
            soillayers=self.soillayers.copy(),
        )

    def plot(
        self,
        size_x: float = 10,
        size_y: float = 12,
    ) -> Figure:
        """Plot the borehole

        Args:
            size_x (float): figure width in inches, default 8
            size_y (float): figure height in inches, default 12
            filepath (str): the path to save the file to
            filename (str): name of the file, defaults to filename from inputfile

        Returns:
            Figure
        """
        fig = plt.figure(figsize=(size_x, size_y))

        ax = fig.add_subplot()
        ax.set_xlim(0, 1)
        plt.title(self.name)
        for soillayer in self.soillayers:
            d = soilcode_to_parameters(soillayer.soilcode)
            ax.add_patch(
                patches.Rectangle(
                    (0.2, soillayer.bottom),
                    0.6,
                    soillayer.height,
                    fill=True,
                    facecolor=d["color"],
                    edgecolor="#000",
                )
            )
            ax.text(0.25, soillayer.bottom, soillayer.soilcode)
        ax.set_ylim(self.bottom - 1, self.top + 1)
        ax.grid(axis="y")

        plt.tight_layout()

        return fig
