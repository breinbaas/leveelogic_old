from pydantic import BaseModel
from typing import List, Optional, Union
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
from matplotlib.pyplot import Figure
import math
from copy import deepcopy
from urllib.request import urlopen

from enum import IntEnum

from .gefxmlreader import XmlCpt
from ..geometry.soillayer import SoilLayer
from ..helpers import xy_to_latlon
from ..settings import (
    DEFAULT_CPT_INTERPRETATION_MIN_LAYERHEIGHT,
    DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO,
)
from ..geometry.soilprofile1 import SoilProfile1
from ..soil.soilcollection import SoilCollection
from ..settings import CPT_QC_MAX, CPT_FR_MAX, BRO_CPT_DOWNLOAD_URL


class ConversionType(IntEnum):
    THREE_TYPE_RULE = 0
    SBT_DUTCH_NON_NORMALIZED = 1
    SBT_DUTCH_NORMALIZED = 2
    NEN_5104 = 3


GEF_COLUMN_Z = 1
GEF_COLUMN_QC = 2
GEF_COLUMN_FS = 3
GEF_COLUMN_U = 6
GEF_COLUMN_Z_CORRECTED = 11

NEN5140 = [
    ["nl_veen", 8.1],
    ["nl_venige_klei", 5],
    ["nl_humeuze_klei", 4],
    ["nl_klei", 2.9],
    ["nl_siltige_klei", 2.5],
    ["nl_zandige_klei", 2.2],
    ["nl_kleiig_zand", 1.8],
    ["nl_siltig_zand", 1.4],
    ["nl_fijn_zand", 1.1],
    ["nl_middelgrof_zand", 0.8],
    ["nl_grof_zand", 0.0],
]


class CptConversionMethod(IntEnum):
    """Defines the conversion methods that are available"""

    THREE_TYPE_RULE = 0
    NL_RF = 1
    ROBERTSON = 2


class CptReadError(Exception):
    """This exception is raised if the passed cpt data is invalid"""

    pass


class Cpt(BaseModel):
    """Class for working with Cone Penetration Tests (gef and xml files)"""

    x: float = 0.0
    y: float = 0.0
    xy: Union[float, float] = (0, 0)
    latlon: Union[float, float] = (0, 0)
    top: float = 0.0
    bottom: float = 0.0

    z: List[float] = []
    qc: List[float] = []
    fs: List[float] = []
    u: List[float] = []
    fr: List[float] = []

    name: str = ""
    filedate: str = ""
    startdate: str = ""
    filename: str = ""
    pre_excavated_depth: float = 0.0

    @classmethod
    def from_bro_id(self, bro_id: str) -> Optional["Cpt"]:
        """Create a Cpt object from a given BRO ID

        Args:
            bro_id (str): The Cpt id in the BRO system

        Raises:
            CptReadError: Error if there is a problem downloading / reading the file

        Returns:
            Cpt: Cpt object if succesful
        """
        URL = f"{BRO_CPT_DOWNLOAD_URL}/{bro_id}"
        try:
            s = urlopen(URL).read()
            return Cpt.from_string(s, suffix=".xml")
        except Exception as e:
            raise CptReadError(
                f"Error reading cpt file from url '{URL}', got error '{e}' "
            )

    @classmethod
    def from_file(self, filename: str) -> Optional["Cpt"]:
        """Create a Cpt object from a gef or xml file

        Args:
            filename (str): The name of the file

        Raises:
            CptReadError: Error if there is a problem downloading / reading the file

        Returns:
            Cpt: Cpt object if succesful
        """
        try:
            data = open(filename, "r", encoding="utf-8", errors="ignore").read()
            return Cpt.from_string(data, Path(filename).suffix.lower())
        except Exception as e:
            raise CptReadError(f"Error reading cpt file '{filename}', got error '{e}' ")

    @classmethod
    def from_string(self, data: str, suffix: str) -> Optional["Cpt"]:
        """Create a Cpt from a given string

        Args:
            data (str): The data in string format
            suffix (str): The file suffix (.gef or .xml)

        Raises:
            CptReadError: Error if there is a problem downloading / reading the file

        Returns:
            Cpt: Cpt object if succesful
        """

        cpt = Cpt()
        if suffix == ".xml":
            try:
                cpt.read_xml(data)
                return cpt
            except Exception as e:
                raise CptReadError(f"Error reading XmlCpt data; '{e}'")
        elif suffix == ".gef":
            try:
                cpt.read_gef(data)
                return cpt
            except Exception as e:
                raise CptReadError(f"Error reading GEFCpt data; '{e}'")
        else:
            raise CptReadError(
                f"Invalir or unsupported filetype '{suffix}', supported are *.gef, *.xml"
            )

    def read_gef(self, data):
        reading_header = True
        metadata = {
            "record_seperator": "",
            "column_seperator": " ",
            "columnvoids": {},
            "columninfo": {},
        }
        lines = data.split("\n")
        for line in lines:
            if reading_header:
                if line.find("#EOH") >= 0:
                    reading_header = False
                else:
                    self._parse_header_line(line, metadata)
            else:
                self._parse_data_line(line, metadata)

        self._post_process()

    def read_xml(self, data):
        """Read an xml file

        Args:
            data (str): The XML file as a string
        """
        xmlcpt = XmlCpt()
        xmlcpt.parse_xml_string(data)

        # now convert to pygef Cpt class and use that logic to read it
        self.startdate = xmlcpt.date.strftime("%Y%m%d")
        self.x = xmlcpt.easting
        self.y = xmlcpt.northing
        self.top = xmlcpt.groundlevel
        self.name = xmlcpt.testid
        xmlcpt.data.depth = xmlcpt.groundlevel - xmlcpt.data.depth
        self.z = xmlcpt.data.depth.to_list()
        if xmlcpt.pre_excavated_depth is not None:
            self.pre_excavated_depth = xmlcpt.pre_excavated_depth
        else:
            self.pre_excavated_depth = 0
        self.qc = xmlcpt.data.coneResistance.to_list()
        self.fs = xmlcpt.data.localFriction.to_list()
        if "porePressureU2" in xmlcpt.data.columns:
            self.u = xmlcpt.data.porePressureU2.to_list()
        else:
            self.u = [0.0 for _ in range(len(self.qc))]
        self._post_process()

    @property
    def length(self) -> float:
        """Returns the length of the Cpt from top to bottom

        Returns:
            float: The length of the Cpt from top to bottom
        """
        return self.top - self.bottom

    @property
    def lat(self) -> float:
        """Returns the latitude of the Cpt

        Returns:
            float: The latitude of the Cpt
        """
        return self.latlon[0]

    @property
    def lon(self) -> float:
        """Returns the longitude of the Cpt

        Returns:
            float: The longitude of the Cpt
        """
        return self.latlon[1]

    @property
    def date(self) -> str:
        """Return the date of the CPT in the following order (if available) startdate, filedata, empty string (no date)

        Args:
            None

        Returns:
            str: date in format YYYYMMDD
        """
        if self.startdate != "":
            return self.startdate
        elif self.filedate != "":
            return self.filedate
        else:
            raise ValueError("This geffile has no date or invalid date information.")

    @property
    def has_u(self) -> bool:
        """
        Does this CPT has waterpressure

        Args:
            None

        Return:
            bool: true is CPT has waterpressure readings, false otherwise
        """
        return max(self.u) > 0 or min(self.u) < 0

    def _post_process(self) -> None:
        """
        Calculate other parameters from the qc and fs values

        Returns:
            None
        """
        self.fr = []

        for qc, fs in zip(self.qc, self.fs):
            if qc == 0.0:
                self.fr.append(CPT_FR_MAX)
            else:
                self.fr.append(fs / qc * 100.0)

        # calculate and set lat lon
        self.latlon = xy_to_latlon(self.x, self.y)
        self.xy = (self.x, self.y)

        # remove nan lines
        zs, qcs, fss, frs, u2s = [], [], [], [], []
        for i, z in enumerate(self.z):
            qc = self.qc[i]
            fs = self.fs[i]
            fr = self.fr[i]
            u2 = self.u[i]

            if np.isnan(z):
                continue
            if np.isnan(qc):
                qc = 0.0
            if np.isnan(fs):
                fs = 0.0
            if np.isnan(fr):
                fr = 0.0
            if np.isnan(u2):
                u2 = 0
            zs.append(self.z[i])
            qcs.append(qc)
            fss.append(fs)
            frs.append(fr)
            u2s.append(u2)

        self.z = zs
        self.qc = qcs
        self.fs = fss
        self.fr = frs
        self.u = u2s

        self.top = round(self.top, 2)
        self.bottom = round(self.z[-1], 2)

    def _parse_header_line(self, line: str, metadata: dict) -> None:
        """Internal function to parse GEF header lines

        Args:
            line (str): The line to parse
            metadata (dict): The metadata object to fill from the header information

        Raises:
            ValueError: Possible value errors
            CptReadError: Possible reading errors

        """
        try:
            args = line.split("=")
            keyword, argline = args[0], args[1]
        except Exception as e:
            raise ValueError(f"Error reading headerline '{line}' -> error {e}")

        keyword = keyword.strip().replace("#", "")
        argline = argline.strip()
        args = argline.split(",")

        if keyword in ["PROCEDURECODE", "REPORTCODE"]:
            if args[0].upper().find("BORE") > -1:
                raise CptReadError("This is a borehole file instead of a Cpt file")
        elif keyword == "RECORDSEPARATOR":
            metadata["record_seperator"] = args[0]
        elif keyword == "COLUMNSEPARATOR":
            metadata["column_seperator"] = args[0]
        elif keyword == "COLUMNINFO":
            try:
                column = int(args[0])
                dtype = int(args[3].strip())
                if dtype == GEF_COLUMN_Z_CORRECTED:
                    dtype = GEF_COLUMN_Z  # use corrected depth instead of depth
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
        elif keyword == "MEASUREMENTVAR":
            if args[0] == "13":
                try:
                    self.pre_excavated_depth = float(args[1])
                except Exception as e:
                    raise ValueError(
                        f"Invalid pre-excavated depth found in line '{line}'. Got error '{e}'"
                    )
        elif keyword == "COLUMNVOID":
            try:
                col = int(args[0].strip())
                metadata["columnvoids"][col - 1] = float(args[1].strip())
            except Exception as e:
                raise ValueError(f"Error reading columnvoid '{line}' -> error {e}")
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
        """Parse a GEF Cpt data line

        Args:
            line (str): The line to parse
            metadata (dict): The metadata to use for parsing

        Raises:
            ValueError: Possible value errors
        """
        try:
            if len(line.strip()) == 0:
                return
            args = (
                line.replace(metadata["record_seperator"], "")
                .strip()
                .split(metadata["column_seperator"])
            )
            args = [
                float(arg.strip())
                for arg in args
                if len(arg.strip()) > 0 and arg.strip() != metadata["record_seperator"]
            ]

            # skip lines that have a columnvoid
            for col_index, voidvalue in metadata["columnvoids"].items():
                if args[col_index] == voidvalue:
                    return

            zcolumn = metadata["columninfo"][GEF_COLUMN_Z]
            qccolumn = metadata["columninfo"][GEF_COLUMN_QC]
            fscolumn = metadata["columninfo"][GEF_COLUMN_FS]

            ucolumn = -1
            if GEF_COLUMN_U in metadata["columninfo"].keys():
                ucolumn = metadata["columninfo"][GEF_COLUMN_U]

            dz = self.top - abs(args[zcolumn])
            self.z.append(dz)

            qc = args[qccolumn]
            if qc <= 0:
                qc = 1e-3
            self.qc.append(qc)
            fs = args[fscolumn]
            if fs <= 0:
                fs = 1e-6
            self.fs.append(fs)

            if ucolumn > -1:
                self.u.append(args[ucolumn])
            else:
                self.u.append(0.0)

        except Exception as e:
            raise ValueError(f"Error reading dataline '{line}' -> error {e}")

    def cut(self, top: float, bottom: float, inline: bool = False) -> Optional["Cpt"]:
        """Create a copy of the Cpt but cut at the given top and bottom

        Args:
            top (float): top boundary of the cpt
            bottom (float): bottom boundary of the cpt
            inline (bool): apply to self (True) or return a new Cpt (False), defaults to False

        Returns:
            Cpt: inline = True -> Copy of the cpt but cut at the given levels else None
        """
        top_idx = -1
        bottom_idx = -1

        for i in range(len(self.z)):
            if self.z[i] <= top:
                top_idx = i
                break

        for i in range(len(self.z) - 1, -1, -1):
            if self.z[i] >= bottom:
                bottom_idx = i + 1
                break

        if top_idx >= bottom_idx:
            raise ValueError(
                f"The given top and bottom parameters result in an empty cpt."
            )

        if inline:
            self.z = self.z[top_idx:bottom_idx]
            self.qc = self.qc[top_idx:bottom_idx]
            self.fs = self.fs[top_idx:bottom_idx]
            self.fr = self.fr[top_idx:bottom_idx]
            self.u = self.u[top_idx:bottom_idx]
            self.bottom = self.z[-1]
            self.top = self.z[0]

        else:
            result = deepcopy(self)
            result.z = result.z[top_idx:bottom_idx]
            result.qc = result.qc[top_idx:bottom_idx]
            result.fs = result.fs[top_idx:bottom_idx]
            result.fr = result.fr[top_idx:bottom_idx]
            result.u = result.u[top_idx:bottom_idx]
            result.bottom = result.z[-1]

            if top > self.top:
                result.top = self.top
            else:
                result.top = result.z[0]

            return result

    def as_numpy(self) -> np.array:
        """
        Return the CPT data as a numpy array with;

        col     value
        0       z
        1       qc
        2       fs
        3       fr
        4       u

        Args:
            None

        Returns:
            np.array: the CPT data as a numpy array"""
        if self.has_u:
            return np.transpose(
                np.array([self.z, self.qc, self.fs, self.fr, self.u], dtype=float)
            )
        else:
            return np.transpose(
                np.array([self.z, self.qc, self.fs, self.fr], dtype=float)
            )

    def as_dataframe(self) -> pd.DataFrame:
        """
        Return the CPT data as a dataframe with columns;
        z, qc, fs, fr, u

        Args:
            None

        Returns:
            pd.DataFrame: the CPT data as a DataFrame"""
        data = self.as_numpy()
        if self.has_u:
            return pd.DataFrame(data=data, columns=["z", "qc", "fs", "fr", "u"])
        else:
            return pd.DataFrame(data=data, columns=["z", "qc", "fs", "fr"])

    def plot_Ic(
        self,
        filename: str = "",
        size_x: float = 10,
        size_y: float = 12,
    ):
        fig = Figure(figsize=(size_x, size_y))

        spec = gridspec.GridSpec(ncols=2, nrows=1, width_ratios=[2, 1])
        z1 = round(self.bottom) - 1.0
        z2 = round(self.top) + 1.0
        ax_qc = fig.add_subplot(spec[0, 0])
        ax_qc.plot(self.qc, self.z, "k")
        ax_qc.set_xlim(0, CPT_QC_MAX)
        ax_qc.set_ylim(z1, z2)
        ax_qc.grid(which="both")
        ax_qc.set_title("Qc [kPa]")

        if self.pre_excavated_depth > 0.0:
            ax_qc.add_patch(
                patches.Rectangle(
                    (0, self.top - self.pre_excavated_depth),
                    CPT_QC_MAX,
                    self.pre_excavated_depth,
                    fill=None,
                    hatch="///",
                )
            )
            ax_qc.text(0, self.top + 0.1, "predrilled")

        MIc = self.to_z_Ic_list()
        ax_Ic = fig.add_subplot(spec[0, 1])
        ax_Ic.add_patch(
            patches.Rectangle(
                (1, z1),
                0.31,
                (z2 - z1),
                color="#eb9d4a",
                fill=True,
            )
        )

        ax_Ic.add_patch(
            patches.Rectangle(
                (1.31, z1),
                0.69,
                (z2 - z1),
                color="#bba35c",
                fill=True,
            )
        )

        ax_Ic.add_patch(
            patches.Rectangle(
                (2.0, z1),
                0.60,
                (z2 - z1),
                color="#7ec4a0",
                fill=True,
            )
        )

        ax_Ic.add_patch(
            patches.Rectangle(
                (2.6, z1),
                0.35,
                (z2 - z1),
                color="#479085",
                fill=True,
            )
        )

        ax_Ic.add_patch(
            patches.Rectangle(
                (2.95, z1),
                0.65,
                (z2 - z1),
                color="#4a5779",
                fill=True,
            )
        )

        ax_Ic.add_patch(
            patches.Rectangle(
                (3.6, z1),
                0.4,
                (z2 - z1),
                color="#b4693f",
                fill=True,
            )
        )

        ax_Ic.set_xlim(1, 4)
        ax_Ic.set_ylim(z1, z2)
        ax_Ic.plot(MIc[:, 1], self.z, "k")
        ax_Ic.grid(which="both")
        ax_Ic.set_title("SBT index [-]")

        fig.suptitle(f"{self.name}")

        if filename == "":
            return fig
        else:
            fig.savefig(filename)

    def plot(
        self,
        filename: str = "",
        size_x: float = 10,
        size_y: float = 12,
        cptconversionmethod: CptConversionMethod = None,
        minimum_layerheight: float = DEFAULT_CPT_INTERPRETATION_MIN_LAYERHEIGHT,
        peat_friction_ratio: float = DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO,
        add_preexcavated_layer: bool = True,
    ) -> Optional[Figure]:
        """Plot the CPT

        Args:
            filename (str): the name of the file to save to, if not set the function will return a Figure object
            size_x (float): figure width in inches, default 8
            size_y (float): figure height in inches, default 12

        Returns:
            Figure if filename is not set
        """
        data = self.as_dataframe()
        fig = Figure(figsize=(size_x, size_y))

        spec = gridspec.GridSpec(ncols=4, nrows=1, width_ratios=[3, 1, 1, 1])

        z1 = round(self.bottom) - 1.0
        z2 = round(self.top) + 1.0

        ax_qc = fig.add_subplot(spec[0, 0])

        data.plot(x="qc", y="z", ax=ax_qc, sharey="col", label="qc [MPa]")
        ax_qc.grid(which="both")
        ax_qc.set_xlim(0, CPT_QC_MAX)
        ax_qc.set_ylim(z1, z2)

        suffix = ""
        if cptconversionmethod is not None:
            sp1 = self.to_soilprofile1(
                minimum_layerheight=minimum_layerheight,
                cptconversionmethod=cptconversionmethod,
                peat_friction_ratio=peat_friction_ratio,
                add_preexcavated_layer=add_preexcavated_layer,
            )

            colordict = SoilCollection().get_color_dict()

            for soillayer in sp1.soillayers:
                if not soillayer.soilcode in colordict.keys():
                    print(
                        f"[ERROR] Missing entry '{soillayer.soilcode}' in the soilcollection"
                    )
                    facecolor = "#ffffff"
                else:
                    facecolor = colordict[soillayer.soilcode]
                ax_qc.add_patch(
                    patches.Rectangle(
                        (0, soillayer.bottom),
                        50,
                        soillayer.height,
                        fill=True,
                        facecolor=facecolor,
                    )
                )
                ax_qc.text(5, soillayer.mid, soillayer.soilcode)

            if cptconversionmethod == CptConversionMethod.THREE_TYPE_RULE:
                suffix = "(threetype rule)"
            elif cptconversionmethod == CptConversionMethod.NL_RF:
                suffix = "(nen 5104)"
            elif cptconversionmethod == CptConversionMethod.ROBERTSON:
                suffix = "(robertson)"
            else:
                raise ValueError(
                    f"Unknown interpretation method '{cptconversionmethod}'"
                )
        else:  # if applicable plot the preexcavated layer
            if self.pre_excavated_depth > 0.0:
                ax_qc.add_patch(
                    patches.Rectangle(
                        (0, self.top - self.pre_excavated_depth),
                        CPT_QC_MAX,
                        self.pre_excavated_depth,
                        fill=None,
                        hatch="///",
                    )
                )
                ax_qc.text(0, self.top + 0.1, "predrilled")

        fig.suptitle(f"{self.name} {suffix}")

        ax_fs = fig.add_subplot(spec[0, 1])
        data.plot(x="fs", y="z", ax=ax_fs, sharey="col", label="fs [MPa]")
        ax_fs.grid(which="both")
        ax_fs.set_xlim(0, 0.2)
        ax_fs.set_ylim(z1, z2)

        ax_fr = fig.add_subplot(spec[0, 2])
        data.plot(x="fr", y="z", ax=ax_fr, sharey="col", label="fr [%]")
        ax_fr.grid(which="both")
        ax_fr.set_xlim(0, 10.0)
        ax_fr.set_ylim(z1, z2)

        if self.has_u:
            ax_u = fig.add_subplot(spec[0, 3])
            data.plot(x="u", y="z", ax=ax_u, sharey="col", label="u [kPa]")
            ax_u.grid(which="both")
            ax_u.set_ylim(z1, z2)

        # plt.tight_layout()
        if filename == "":
            return fig
        else:
            fig.savefig(filename)

    def filter(
        self,
        top: float,
        minimum_layerheight: float = DEFAULT_CPT_INTERPRETATION_MIN_LAYERHEIGHT,
    ) -> np.array:
        """Return the CPT data as a numpy array with;

        col     value
        0       ztop
        1       zbot
        2       qc
        3       fs
        4       fr
        5       u

        Args:
            top (float): the z value to start from
            minimum_layerheight (float): the minimal layerheight to use

        Returns:
            np.array: the CPT data as a numpy array"""
        a = self.as_numpy()

        ls = np.arange(
            top,
            self.z[-1] - DEFAULT_CPT_INTERPRETATION_MIN_LAYERHEIGHT,
            -minimum_layerheight,
        )

        result = []
        for i in range(1, len(ls)):
            ztop = ls[i - 1]
            zbot = ls[i]
            selection = a[(a[:, 0] <= ztop) & (a[:, 0] >= zbot)]
            layer = np.array([ztop, zbot])
            mean = np.mean(selection[:, 1:], axis=0)
            result.append(np.concatenate((layer, mean), axis=None))

        return np.array(result)

    def _nen_5014(
        self,
        minimum_layerheight: float,
        peat_friction_ratio: float = DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO,
        add_preexcavated_layer=True,
    ) -> List[SoilLayer]:
        """
        Conversion function for the rule as found in CUR162 electric cone

        Args:
            minimum_layerheight (float): the minimum layer height
            peat_friction_ratio (float):
            add_preexcavated_layer (bool): if we have a pre excaveted depth and this is True than we will add a soillayer
                with soilcode 'preexcavated' on top of the result. If False then we will ignore the fact that the
                soil is preexcavated and simply interpret the data as a soiltype. Defaults to True

        Returns:
            List[SoilLayer]: the list of soillayers
        """
        soillayers = []
        if self.pre_excavated_depth > 0 and add_preexcavated_layer:
            soillayers.append(
                SoilLayer(
                    top=self.top,
                    bottom=self.top - self.pre_excavated_depth,
                    soilcode="preexcavated",
                )
            )
            cptdata = self.filter(
                self.top - self.pre_excavated_depth, minimum_layerheight
            )
        else:
            cptdata = self.filter(self.top, minimum_layerheight)

        for row in cptdata:
            fr = row[4]

            if fr >= peat_friction_ratio:
                soillayers.append(
                    SoilLayer(
                        top=round(row[0], 2),
                        bottom=round(row[1], 2),
                        soilcode="peat",
                    )
                )
            else:
                for soilcode, _fr in NEN5140:
                    if fr >= _fr:
                        soillayers.append(
                            SoilLayer(
                                top=round(row[0], 2),
                                bottom=round(row[1], 2),
                                soilcode=soilcode,
                            )
                        )
                        break

        return soillayers

    def _three_type_rule(
        self,
        minimum_layerheight: float,
        peat_friction_ratio: float = DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO,
        add_preexcavated_layer=True,
    ) -> List[SoilLayer]:
        """
        Conversion function for the three type rule

        Args:
            minimum_layerheight (float): the minimum layer height
            peat_friction_ratio (float):
            add_preexcavated_layer (bool): if we have a pre excaveted depth and this is True than we will add a soillayer
                with soilcode 'preexcavated' on top of the result. If False then we will ignore the fact that the
                soil is preexcavated and simply interpret the data as a soiltype. Defaults to True

        Returns:
            List[SoilLayer]: the list of soillayers
        """
        #     0     1     2       3       4      5
        # get ztop, zbot, qc_avg, fs_avg, fr_avg u_avg matrix
        soillayers = []

        # if we have a pre excaveted depth and we want to include that than that layer will be placed on top
        if self.pre_excavated_depth > 0 and add_preexcavated_layer:
            soillayers.append(
                SoilLayer(
                    top=self.top,
                    bottom=self.top - self.pre_excavated_depth,
                    soilcode="preexcavated",
                )
            )
            cptdata = self.filter(
                self.top - self.pre_excavated_depth, minimum_layerheight
            )
        else:
            cptdata = self.filter(self.top, minimum_layerheight)

        for row in cptdata:
            x = row[4]
            y = math.log(row[2])

            if x < 0:
                x = 0
            if x > 10:
                x = 10
            if y < -1:
                y = -1
            if y > 2:
                y = 2

            soilcode = ""
            if y <= x * 0.4 - 2:
                if x < 4:
                    soilcode = "clay"
                else:
                    soilcode = "peat"
            elif y > x * 0.4 - 0.30103:
                soilcode = "sand"
            else:
                soilcode = "clay"

            # override if necessary
            if row[4] >= peat_friction_ratio:
                soilcode = "peat"

            soillayers.append(
                SoilLayer(
                    top=round(row[0], 2), bottom=round(row[1], 2), soilcode=soilcode
                )
            )

        return soillayers

    def _robertson(
        self,
        minimum_layerheight: float,
        peat_friction_ratio: float = DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO,
        add_preexcavated_layer=True,
    ) -> List[SoilLayer]:
        """Conversion function as found in http://www.cpt-robertson.com/PublicationsPDF/2-56%20RobSBT.pdf

        Args:
            minimum_layerheight (float): _description_
            peat_friction_ratio (float, optional): _description_. Defaults to 1e9.
            add_preexcavated_layer (bool, optional): _description_. Defaults to True.

        Returns:
            List[SoilLayer]: _description_
        """
        soillayers = []
        if self.pre_excavated_depth > 0 and add_preexcavated_layer:
            soillayers.append(
                SoilLayer(
                    top=self.top,
                    bottom=self.top - self.pre_excavated_depth,
                    soilcode="preexcavated",
                )
            )
            cptdata = self.filter(
                self.top - self.pre_excavated_depth, minimum_layerheight
            )
        else:
            cptdata = self.filter(self.top, minimum_layerheight)

        for row in cptdata:
            qc = row[2]
            fr = row[4]
            isbt = (3.47 - np.log10(qc * 1000 / 100)) ** 2 + (np.log10(fr + 1.22)) ** 2
            isbt = isbt**0.5

            if isbt > 3.6:
                soilcode = "organic_clay"
            elif isbt > 2.95:
                soilcode = "clay"
            elif isbt > 2.60:
                soilcode = "silty_clay"
            elif isbt > 2.05:
                soilcode = "silty_sand"
            elif isbt > 1.31:
                soilcode = "sand"
            else:
                soilcode = "dense_sand"

            if fr >= peat_friction_ratio:
                soilcode = "peat"

            soillayers.append(
                SoilLayer(
                    top=round(row[0], 2), bottom=round(row[1], 2), soilcode=soilcode
                )
            )

        return soillayers

    def to_z_Ic_list(self) -> np.array:
        """Convert the reading to the soil behaviour type index Ic

        Note that we do NOT use the normalized cone resistance value!
        According to https://static.rocscience.cloud/assets/verification-and-theory/Settle3/CPT-Theory-Manual.pdf
        we use qc = qt even if u2 is available

        Returns:
            np.array: Numpy array with columns depth [0] and Ic [1]
        """
        a = self.as_numpy()
        ic = (3.47 - np.log10(a[:, 1] * 1000 / 100)) ** 2 + (
            np.log10(a[:, 3] + 1.22)
        ) ** 2
        ic = ic**0.5

        return np.column_stack((a[:, 0], ic))

    def to_soilprofile1(
        self,
        cptconversionmethod: CptConversionMethod,
        minimum_layerheight: float = DEFAULT_CPT_INTERPRETATION_MIN_LAYERHEIGHT,
        peat_friction_ratio: float = DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO,
        add_preexcavated_layer: bool = True,
        left: float = 0.0,
        right: float = 0.0,
    ) -> SoilProfile1:
        """Convert a Cpt to a 1D soilprofile

        Args:
            cptconversionmethod (CptConversionMethod): The conversion method to use
            minimum_layerheight (float, optional): The minimum layer height. Defaults to DEFAULT_MINIMUM_LAYERHEIGHT
            peat_friction_ratio (float): if the fr >= peat_friction_ratio the soillayer will be defined as peat
            add_preexcavated_layer (bool, optional): Add the preexacavated depth as a seperate layer with soilcode 'preexcavated'. Defaults to True.

        Returns:
            SoilProfile1: One dimension soilprofile
        """
        soilprofile1 = SoilProfile1(left=left, right=right)
        soilprofile1.lat = self.latlon[0]
        soilprofile1.lon = self.latlon[1]

        if cptconversionmethod == CptConversionMethod.THREE_TYPE_RULE:
            soilprofile1.soillayers = self._three_type_rule(
                minimum_layerheight=minimum_layerheight,
                peat_friction_ratio=peat_friction_ratio,
                add_preexcavated_layer=add_preexcavated_layer,
            )
            soilprofile1._merge()
        elif cptconversionmethod == CptConversionMethod.NL_RF:
            soilprofile1.soillayers = self._nen_5014(
                minimum_layerheight=minimum_layerheight,
                peat_friction_ratio=peat_friction_ratio,
                add_preexcavated_layer=add_preexcavated_layer,
            )
            soilprofile1._merge()
        elif cptconversionmethod == CptConversionMethod.ROBERTSON:
            soilprofile1.soillayers = self._robertson(
                minimum_layerheight,
                peat_friction_ratio=peat_friction_ratio,
                add_preexcavated_layer=add_preexcavated_layer,
            )
            soilprofile1._merge()
        else:
            raise ValueError(
                f"Invalid or unimplemented CptConversionMethod {cptconversionmethod}"
            )

        return soilprofile1
