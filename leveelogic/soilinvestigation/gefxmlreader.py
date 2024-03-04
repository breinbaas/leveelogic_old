"""
Script om sonderingen en boringen vanuit GEF of XML (BRO) in te lezen en te plotten
"""

__author__ = "Thomas van der Linden"
__credits__ = ""
__license__ = "MPL-2.0"
__version__ = ""
__maintainer__ = "Thomas van der Linden"
__email__ = "t.van.der.linden@amsterdam.nl"
__status__ = "Dev"

from dataclasses import dataclass
from typing import OrderedDict
import pandas as pd
from io import StringIO
import numpy as np
import re
from datetime import datetime
import xml.etree.ElementTree as ET


@dataclass
class XmlCpt:
    """XmlCpt code by "Thomas van der Linden"""

    def __init__(self):
        self.easting = None
        self.northing = None
        self.groundlevel = -9999
        self.srid = None
        self.testid = None
        self.date = None
        self.finaldepth = None
        self.removedlayers = {}
        self.data = None
        self.filename = None
        self.companyid = None
        self.projectid = None
        self.projectname = None
        self.pre_excavated_depth = None

    def parse_xml_string(self, xml_string: str):
        tree = ET.ElementTree(ET.fromstring(xml_string))
        self._parse_tree(tree)

    def load_xml_file(self, xmlFile):
        tree = ET.ElementTree()
        tree.parse(xmlFile)
        self._parse_tree(tree)

    def _parse_tree(self, tree):
        root = tree.getroot()

        for element in root.iter():
            if "broId" in element.tag:
                self.testid = element.text

            if "deliveredLocation" in element.tag:
                location = {
                    re.sub(r"{.*}", "", p.tag): re.sub(r"\n\s*", "", p.text)
                    for p in element.iter()
                    if p.text is not None
                }
                self.easting = float(location["pos"].split()[0])
                self.northing = float(location["pos"].split()[1])

            elif "deliveredVerticalPosition" in element.tag:
                verticalPosition = {
                    re.sub(r"{.*}", "", p.tag): re.sub(r"\n\s*", "", p.text)
                    for p in element.iter()
                    if p.text is not None
                }
                self.groundlevel = float(verticalPosition["offset"])

            elif "finalDepth" in element.tag:
                self.finaldepth = float(element.text)

            elif "researchReportDate" in element.tag:
                date = {
                    re.sub(r"{.*}", "", p.tag): re.sub(r"\n\s*", "", p.text)
                    for p in element.iter()
                    if p.text is not None
                }
                try:  # een datum is niet verplicht
                    self.date = datetime.strptime(date["date"], "%Y-%m-%d")
                except:
                    pass

            # er kan een dissipatietest inzitten, hiermee wordt alleen de cpt ingelezen. Die staat in dissipationTest
            elif "conePenetrationTest" in element.tag:
                for child in element.iter():
                    if "values" in child.tag:
                        self.data = child.text

            elif "removedLayer" in element.tag:
                self.removedlayers = {
                    re.sub(r"{.*}", "", p.tag): re.sub(r"\n\s*", "", p.text)
                    for p in element.iter()
                    if p.text is not None
                }

            elif "predrilledDepth" in element.tag:
                if element.text is not None:
                    self.pre_excavated_depth = float(element.text)
                else:
                    self.pre_excavated_depth = 0.0

        dataColumns = [
            "penetrationLength",
            "depth",
            "elapsedTime",
            "coneResistance",
            "correctedConeResistance",
            "netConeResistance",
            "magneticFieldStrengthX",
            "magneticFieldStrengthY",
            "magneticFieldStrengthZ",
            "magneticFieldStrengthTotal",
            "electricalConductivity",
            "inclinationEW",
            "inclinationNS",
            "inclinationX",
            "inclinationY",
            "inclinationResultant",
            "magneticInclination",
            "magneticDeclination",
            "localFriction",
            "poreRatio",
            "temperature",
            "porePressureU1",
            "porePressureU2",
            "porePressureU3",
            "frictionRatio",
        ]

        self.data = pd.read_csv(
            StringIO(self.data), names=dataColumns, sep=",", lineterminator=";"
        )
        self.data = self.data.replace(-999999, np.nan)

        self.check_depth()

        self.data.sort_values(by="depth", inplace=True)

    def check_depth(self):
        # soms is er geen diepte, maar wel sondeerlengte aanwezig
        # sondeerlengte als diepte gebruiken is goed genoeg als benadering
        if "depth" not in self.data.columns or self.data["depth"].isna().all():
            # verwijder de lege kolommen om het vervolg eenvoudiger te maken
            self.data.dropna(axis=1, how="all", inplace=True)
            # bereken diepte als inclinatie bepaald is
            if "penetrationLength" in self.data.columns:
                self.data.sort_values("penetrationLength", inplace=True)
                if "inclinationResultant" in self.data.columns:
                    self.data["correctedPenetrationLength"] = self.data[
                        "penetrationLength"
                    ].diff().abs() * np.cos(
                        np.deg2rad(self.data["inclinationResultant"])
                    )
                    self.data["depth"] = self.data[
                        "correctedPenetrationLength"
                    ].cumsum()
                elif (
                    "inclinationEW" in self.data.columns
                    and "inclinationNS" in self.data.columns
                ):
                    z = self.data["penetrationLength"].diff().abs()
                    x = z * np.tan(np.deg2rad(self.data["inclinationEW"]))
                    y = z * np.tan(np.deg2rad(self.data["inclinationNS"]))
                    self.data["inclinationResultant"] = np.rad2deg(
                        np.cos(np.sqrt(x**2 + y**2 + z**2) / z)
                    )
                    self.data["correctedPenetrationLength"] = self.data[
                        "penetrationLength"
                    ].diff().abs() * np.cos(
                        np.deg2rad(self.data["inclinationResultant"])
                    )
                    self.data["depth"] = self.data[
                        "correctedPenetrationLength"
                    ].cumsum()
                elif "inclinationX" and "inclinationY" in self.data.columns:
                    z = self.data["penetrationLength"].diff().abs()
                    x = z * np.tan(np.deg2rad(self.data["inclinationX"]))
                    y = z * np.tan(np.deg2rad(self.data["inclinationY"]))
                    self.data["inclinationResultant"] = np.rad2deg(
                        np.cos(np.sqrt(x**2 + y**2 + z**2) / z)
                    )
                    self.data["correctedPenetrationLength"] = self.data[
                        "penetrationLength"
                    ].diff().abs() * np.cos(
                        np.deg2rad(self.data["inclinationResultant"])
                    )
                    self.data["depth"] = self.data[
                        "correctedPenetrationLength"
                    ].cumsum()
                # anders is de diepte gelijk aan de penetration length
                else:
                    self.data["depth"] = self.data["penetrationLength"].abs()


@dataclass
class XmlBorehole:
    def __init__(self):
        self.projectid = None
        self.projectname = None
        self.companyid = None
        self.testid = None
        self.easting = None
        self.northing = None
        self.groundlevel = None
        self.srid = None
        self.testid = None
        self.date = None
        self.finaldepth = None
        self.soillayers = {}
        self.analyses = []
        self.metadata = {}
        self.descriptionquality = None

    def to_gef(self, output_file: str):
        gef_string = self.to_gef_string()
        f = open(output_file, "w")
        f.write(gef_string)
        f.close()

    def to_gef_string(self) -> str:
        s = "#GEFID= 1, 1, 0\n"
        s += "#FILEOWNER= LeveeLogic\n"
        s += (
            f"#FILEDATE= {self.date.year}, {self.date.month:02d}, {self.date.day:02d}\n"
        )
        s += "#PROJECTID= UNKNOWN\n"
        s += "#COLUMN= 2\n"
        s += "#COLUMNINFO= 1, m, Laag van, 1\n"
        s += "#COLUMNINFO= 2, m, Laag tot, 2\n"
        s += "#COMPANYID= -, -, 31\n"
        s += "#DATAFORMAT= ASCII\n"
        s += "#COLUMNSEPARATOR= ;\n"
        s += f"#LASTSCAN= {self.soillayers['veld'].shape[0]}\n"
        s += f"#XYID= 28992, {self.easting}, {self.northing}\n"
        s += f"#ZID= 31000, {self.groundlevel}\n"
        s += "#PROCEDURECODE= GEF-BORE-Report, 1, 0, 0, -\n"
        s += f"#TESTID= {self.testid}\n"
        s += f"#MEASUREMENTTEXT= 16, {self.date.year}-{self.date.month:02d}-{self.date.day:02d}, datum boring\n"
        s += "#REPORTCODE= GEF-BORE-Report, 1, 0, 0, -\n"
        s += "#OS= DOS\n"
        s += "#LANGUAGE= NL\n"
        s += "#EOH=\n"

        for _, row in self.soillayers["veld"].iterrows():
            top = row["upper_NAP"]
            bot = row["lower_NAP"]
            soilname = row["soilName"]
            try:
                sand = row["sandMedianClass"]
            except:
                sand = ""

            try:
                organic = row["organicMatterContentClass"]
            except:
                organic = ""

            if type(sand) != str and np.isnan(sand):
                sand = ""

            if type(organic) != str and np.isnan(organic):
                organic = ""

            s += f"{top:.2f};{bot:.2f};{soilname};{sand};;{organic};;\n"

        return s

    def parse_xml_string(self, xml_string: str):
        tree = ET.ElementTree(ET.fromstring(xml_string))
        self._parse_tree(tree)

    def load_xml_file(self, xmlFile):
        # lees een boring in vanuit een BRO XML
        tree = ET.ElementTree()
        tree.parse(xmlFile)
        self._parse_tree(tree)

    def _parse_tree(self, tree):
        root = tree.getroot()

        for element in root.iter():
            if "broId" in element.tag or "requestReference" in element.tag:
                self.testid = element.text

            if "deliveredLocation" in element.tag:
                location = {
                    re.sub(r"{.*}", "", p.tag): re.sub(r"\n\s*", "", p.text)
                    for p in element.iter()
                    if p.text is not None
                }
                self.easting = float(location["pos"].split()[0])
                self.northing = float(location["pos"].split()[1])

            elif "deliveredVerticalPosition" in element.tag:
                verticalPosition = {
                    re.sub(r"{.*}", "", p.tag): re.sub(r"\n\s*", "", p.text)
                    for p in element.iter()
                    if p.text is not None
                }
                self.groundlevel = float(verticalPosition["offset"])

            elif "finalDepthBoring" in element.tag:
                self.finaldepth = float(element.text)

            elif "descriptionReportDate" in element.tag:
                date = {
                    re.sub(r"{.*}", "", p.tag): re.sub(r"\n\s*", "", p.text)
                    for p in element.iter()
                    if p.text is not None
                }
                self.date = datetime.strptime(date["date"], "%Y-%m-%d")

            elif "descriptiveBoreholeLog" in element.tag:
                for child in element.iter():
                    if "descriptionQuality" in child.tag:
                        descriptionquality = child.text
                    elif "descriptionLocation" in child.tag:
                        descriptionLocation = child.text
                        soillayers = []
                    elif "layer" in child.tag:
                        soillayers.append(
                            {
                                re.sub(r"{.*}", "", p.tag): re.sub(r"\s*", "", p.text)
                                for p in child.iter()
                                if p.text is not None
                            }
                        )
                # zet soillayers om in dataframe om het makkelijker te verwerken
                self.soillayers[descriptionLocation] = pd.DataFrame(soillayers)

            elif "boreholeSampleAnalysis" in element.tag:
                for child in element.iter():
                    if "investigatedInterval" in child.tag:
                        self.analyses.append(
                            {
                                re.sub(r"{.*}", "", p.tag): re.sub(r"\s*", "", p.text)
                                for p in child.iter()
                                if p.text is not None
                            }
                        )

        self.metadata = {
            "easting": self.easting,
            "northing": self.northing,
            "groundlevel": self.groundlevel,
            "testid": self.testid,
            "date": self.date,
            "finaldepth": self.finaldepth,
        }

        for descriptionLocation, soillayers in self.soillayers.items():
            # voeg de componenten toe t.b.v. plot
            self.soillayers[descriptionLocation] = self.add_components(soillayers)

            # specialMaterial was voor het maken van de componenten op NBE gezet, nu weer terug naar de oorspronkelijke waarde
            if "specialMaterial" in soillayers.columns:
                self.soillayers[descriptionLocation][
                    self.soillayers[descriptionLocation]["soilName"] == "NBE"
                ]["soilName"] = soillayers["specialMaterial"]

            # voeg kolommen toe met absolute niveaus (t.o.v. NAP)
            self.soillayers[descriptionLocation]["upperBoundary"] = pd.to_numeric(
                soillayers["upperBoundary"]
            )
            self.soillayers[descriptionLocation]["lowerBoundary"] = pd.to_numeric(
                soillayers["lowerBoundary"]
            )

            self.soillayers[descriptionLocation]["upper_NAP"] = (
                self.groundlevel - soillayers["upperBoundary"]
            )
            self.soillayers[descriptionLocation]["lower_NAP"] = (
                self.groundlevel - soillayers["lowerBoundary"]
            )

    def add_components(self, soillayers):
        # voeg verdeling componenten toe
        # van https://github.com/cemsbv/pygef/blob/master/pygef/broxml.py
        material_components = [
            "gravel_component",
            "sand_component",
            "clay_component",
            "loam_component",
            "peat_component",
            "silt_component",
            "special_material",
        ]
        soil_names_dict_lists = {
            "betonOngebroken": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],  # specialMaterial
            "grind": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "humeuzeKlei": [0.0, 0.0, 0.9, 0.0, 0.1, 0.0],
            "keitjes": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "klei": [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
            "kleiigVeen": [0.0, 0.0, 0.3, 0.0, 0.7, 0.0],
            "kleiigZand": [0.0, 0.7, 0.3, 0.0, 0.0, 0.0],
            "kleiigZandMetGrind": [0.05, 0.65, 0.3, 0.0, 0.0, 0.0],
            "NBE": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],  # specialMaterial
            "puin": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],  # specialMaterial
            "silt": [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            "siltigZand": [0.0, 0.7, 0.0, 0.0, 0.0, 0.3],
            "siltigZandMetGrind": [0.05, 0.65, 0.0, 0.0, 0.0, 0.3],
            "sterkGrindigZand": [0.3, 0.7, 0.0, 0.0, 0.0, 0.0],
            "sterkGrindigeKlei": [0.3, 0.0, 0.7, 0.0, 0.0, 0.0],
            "sterkSiltigZand": [0.0, 0.7, 0.0, 0.0, 0.0, 0.3],
            "sterkZandigGrind": [0.7, 0.3, 0.0, 0.0, 0.0, 0.0],
            "sterkZandigSilt": [0.0, 0.3, 0.0, 0.0, 0.0, 0.7],
            "sterkZandigeKlei": [0.0, 0.3, 0.7, 0.0, 0.0, 0.0],
            "sterkZandigeKleiMetGrind": [0.05, 0.3, 0.65, 0.0, 0.0, 0.0],
            "sterkZandigVeen": [0.0, 0.3, 0.0, 0.0, 0.7, 0.0],
            "veen": [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            "zand": [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            "zwakGrindigZand": [0.1, 0.9, 0.0, 0.0, 0.0, 0.0],
            "zwakGrindigeKlei": [0.1, 0.0, 0.9, 0.0, 0.0, 0.0],
            "zwakSiltigZand": [0.0, 0.9, 0.0, 0.0, 0.0, 0.1],
            "zwakSiltigeKlei": [0.0, 0.0, 0.9, 0.0, 0.0, 0.1],
            "zwakZandigGrind": [0.9, 0.1, 0.0, 0.0, 0.0, 0.0],
            "zwakZandigSilt": [0.0, 0.9, 0.0, 0.0, 0.0, 0.1],
            "zwakZandigVeen": [0.0, 0.1, 0.0, 0.0, 0.9, 0.0],
            "zwakZandigeKlei": [0.0, 0.1, 0.9, 0.0, 0.0, 0.0],
            "zwakZandigeKleiMetGrind": [0.05, 0.1, 0.85, 0.0, 0.0, 0.0],
        }

        # voor sorteren op bijdrage is het handiger om een dictionary te maken
        soil_names_dict_dicts = {}
        for key, value in soil_names_dict_lists.items():
            soil_names_dict_dicts[key] = dict(
                sorted({v: i for i, v in enumerate(value)}.items(), reverse=True)
            )

        soillayers["soilName"] = np.where(
            soillayers["geotechnicalSoilName"].isna(),
            "NBE",
            soillayers["geotechnicalSoilName"],
        )
        # voeg de componenten toe
        soillayers["components"] = soillayers["soilName"].map(soil_names_dict_dicts)
        return soillayers
