from typing import List, Dict
from pathlib import Path

from ..models.datamodel import DataModel
from .soil import Soil

DEFAULT_CPT_INTERPRETATION_SOILCODES = {
    "preexcavated": Soil(
        code="preexcavated",
        color="#54575c",
        y_dry=14.0,
        y_sat=14.0,
        cohesion=2.0,
        friction_angle=20.0,
    ),
    "unknown": Soil(
        code="unknown",
        color="#696969",
        y_dry=14.0,
        y_sat=14.0,
        cohesion=2.0,
        friction_angle=20.0,
    ),
    "top_material": Soil(
        code="top_material",
        color="#696969",
        y_dry=15.0,
        y_sat=15.0,
        cohesion=2.0,
        friction_angle=22.0,
    ),
    "bottom_material": Soil(
        code="bottom_material",
        color="#808080",
        y_dry=17.0,
        y_sat=19.0,
        cohesion=0.0,
        friction_angle=30.0,
    ),  # NL_RF (NEN5104)
    "nl_veen": Soil(
        code="nl_veen",
        color="#786926",
        y_dry=10.0,
        y_sat=10.0,
        cohesion=1.5,
        friction_angle=17.5,
    ),
    "nl_grof_zand": Soil(
        code="nl_grof_zand",
        color="#faff00",
        y_dry=19.0,
        y_sat=21.0,
        cohesion=0.0,
        friction_angle=35.0,
    ),
    "nl_middelgrof_zand": Soil(
        code="nl_middelgrof_zand",
        color="#e0e342",
        y_dry=18.0,
        y_sat=20.0,
        cohesion=0.0,
        friction_angle=32.5,
    ),
    "nl_fijn_zand": Soil(
        code="nl_fijn_zand",
        color="#e6e876",
        y_dry=17.0,
        y_sat=19.0,
        cohesion=0.0,
        friction_angle=30.0,
    ),
    "nl_kleiig_zand": Soil(
        code="nl_kleiig_zand",
        color="#9fa12d",
        y_dry=16.0,
        y_sat=18.0,
        cohesion=1.0,
        friction_angle=30.0,
    ),
    "nl_siltig_zand": Soil(
        code="nl_siltig_zand",
        color="#596b15",
        y_dry=16.0,
        y_sat=17.0,
        cohesion=2.0,
        friction_angle=27.5,
    ),
    "nl_zandige_klei": Soil(
        code="nl_zandige_klei",
        color="#596b15",
        y_dry=16.0,
        y_sat=16.0,
        cohesion=3.0,
        friction_angle=27.5,
    ),
    "nl_siltige_klei": Soil(
        code="nl_siltige_klei",
        color="#3c6318",
        y_dry=15.0,
        y_sat=15.0,
        cohesion=4.0,
        friction_angle=25.0,
    ),
    "nl_klei": Soil(
        code="nl_klei",
        color="#39bf1b",
        y_dry=15.0,
        y_sat=15.0,
        cohesion=5.0,
        friction_angle=25.0,
    ),
    "nl_venige_klei": Soil(
        code="nl_venige_klei",
        color="#7d6b0f",
        y_dry=14.0,
        y_sat=14.0,
        cohesion=3.0,
        friction_angle=20.0,
    ),
    "nl_humeuze_klei": Soil(
        code="nl_humeuze_klei",
        color="#7d6b0f",
        y_dry=14.0,
        y_sat=14.0,
        cohesion=3.0,
        friction_angle=20.0,
    ),
    "peat": Soil(
        code="peat",
        color="#786926",
        y_dry=10.0,
        y_sat=10.0,
        cohesion=1.5,
        friction_angle=17.5,
    ),
    "organic_clay": Soil(
        code="organic_clay",
        color="#a3de2f",
        y_dry=14.0,
        y_sat=14.0,
        cohesion=2.0,
        friction_angle=20.0,
    ),
    "clay": Soil(
        code="clay",
        color="#3c6318",
        y_dry=15.0,
        y_sat=15.0,
        cohesion=5.0,
        friction_angle=25.0,
    ),
    "silty_clay": Soil(
        code="silty_clay",
        color="#596b15",
        y_dry=15.0,
        y_sat=15.0,
        cohesion=3.0,
        friction_angle=25.0,
    ),
    "silty_sand": Soil(
        code="silty_sand",
        color="#9fa12d",
        y_dry=16.0,
        y_sat=18.0,
        cohesion=1.0,
        friction_angle=27.5,
    ),
    "sand": Soil(
        code="sand",
        color="#e6e876",
        y_dry=17.0,
        y_sat=19.0,
        cohesion=0.0,
        friction_angle=30.0,
    ),
    "dense_sand": Soil(
        code="dense_sand",
        color="#fcf403",
        y_dry=19.0,
        y_sat=21.0,
        cohesion=0.0,
        friction_angle=35.0,
    ),
}


class SoilCollectionError(Exception):
    """This exception is raised if there is a problem with the soilcollection"""

    pass


class SoilCollection(DataModel):
    """Class to store a colletion of soil objects"""

    soils: List[Soil] = [v for _, v in DEFAULT_CPT_INTERPRETATION_SOILCODES.items()]
    aliases: Dict = {}

    @classmethod
    def from_csv(obj, filename: str) -> "SoilCollection":
        """Generate a soilcollection from a csv file. The expected format is a header followed
        by lines with the parameters 'code, color, y_dry, y_sat, cohesion, friction angle, dilatancy angle'
        If an error is found a SoilCollectionError is raised with the error.

        Args:
            filename (str): The filepath and filename of the file

        Returns:
            SoilCollection: The resulting soilcollection
        """
        result = SoilCollection()
        result.clear()
        lines = open(filename, "r").readlines()
        for line in lines[1:]:
            if line.strip() == "":
                continue
            args = [s.strip() for s in line.split(",")]
            try:
                result.soils.append(
                    Soil(
                        code=args[0],
                        color=args[1],
                        y_dry=float(args[2]),
                        y_sat=float(args[3]),
                        cohesion=float(args[4]),
                        friction_angle=float(args[5]),
                    )
                )
            except Exception as e:
                raise SoilCollectionError(e)
        return result

    def aliases_from_csv(self, filename: str):
        """Read rows of aliases from a csv file. The expected format is a header followed
        by lines with soilcode, alias

        Args:
            filename (str): name of and path to the file
        """
        lines = open(filename, "r").readlines()
        for line in lines[1:]:
            args = [s.strip() for s in line.split(",")]
            try:
                self.add_alias(args[0], args[1])
            except Exception as e:
                raise SoilCollectionError(e)

    def add_alias(self, alias: str, soilcode: str):
        """Add an alias to allow users to use the same soilcode for multiple or predefined
        soil names

        Args:
            soilcode (str): The soilcode in the current collection
            alias (str): The alias to use for this soilcode

        Raises:
            ValueError: if the soilcode is not found an error will be raised
        """
        if not self.has_soilcode(soilcode):
            raise ValueError(
                f"Trying to set an alias for a unknown soilcode '{soilcode}'"
            )

        if not alias == "" and alias not in self.aliases.keys():
            self.aliases[alias] = soilcode

    def add(self, soil: Soil) -> None:
        """Add a soiltype to the collections

        Args:
            soil (Soil): the soil that needs to be added

        Returns:
            nothing
        """
        for s in self.soils:
            if s.code == soil.code:  # existing code, remove the old one
                self.soils.remove(s)

        self.soils.append(soil)

    def clear(self) -> None:
        """Clears all existing soils"""
        self.soils.clear()

    def reset(self) -> None:
        """Clears all soils and then puts back all the default soils"""
        self.clear()
        self.soils = [v for _, v in DEFAULT_CPT_INTERPRETATION_SOILCODES.items()]

    def get(self, soilcode: str) -> Soil:
        if soilcode in self.aliases:
            soilcode = self.aliases[soilcode]

        for soil in self.soils:
            if soil.code == soilcode:
                return soil
        raise ValueError(f"Unknown soilcode '{soilcode}' requested")

    def has_soilcode(self, soilcode: str) -> bool:
        """Check if the soilcode is available in the soilcollection

        Args:
            soilcode (str): The code of the soil

        Returns:
            bool: True if the soilcode is in the soilcollection, False otherwise
        """
        return soilcode in [s.code for s in self.soils]

    def get_color_dict(self) -> Dict[str, str]:
        """Get a dictionary with the available soilcodes as keys and the color
        as value

        Returns:
            Dict[str, str]: A dictionary with soilcodes and soilcolors
        """
        return {s.code.lower(): s.color for s in self.soils}

    def to_csv(self, filepath: str, filename: str) -> None:
        """Generate a CSV file out of this soilcollection

        Args:
            filepath (str): Path to write to
            filename (str): File to write to
        """
        f = open(Path(filepath) / filename, "w")
        f.write("code,color,y_dry,y_sat,cohesion,friction_angle\n")
        for soil in self.soils:
            f.write(
                f"{soil.code},{soil.color},{soil.y_dry},{soil.y_sat},{soil.cohesion},{soil.friction_angle}\n"
            )
        f.close()
