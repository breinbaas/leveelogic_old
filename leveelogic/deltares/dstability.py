from pydantic import BaseModel, DirectoryPath, FilePath
from enum import IntEnum
from pathlib import Path
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from typing import Dict, List, Tuple, Union, BinaryIO, Optional
from dotenv import load_dotenv
import os
import subprocess
from math import nan

from ..geolib.soils.soil import (
    SoilWeightParameters,
    MohrCoulombParameters,
    ShearStrengthModelTypePhreaticLevel,
)
from ..geolib.geometry.one import Point
from ..geolib.models.dstability import DStabilityModel
from ..geolib.models.dstability.internal import (
    PersistableHeadLine,
    PersistablePoint,
    ShearStrengthModelTypePhreaticLevelInternal,
    UpliftVanParticleSwarmResult,
    BishopBruteForceResult,
    SpencerGeneticAlgorithmResult,
    AnalysisTypeEnum,
    Soil,
    SoilVisualisation,
    WaternetCreatorSettings,
)
from ..geometry.characteristic_point import (
    CharacteristicPoint,
    CharacteristicPointType,
)
from ..soil.soilcollection import SoilCollection
from ..geometry.soilprofileN import SoilProfileN
from ..geometry.soilprofile1 import SoilProfile1
from ..helpers import polyline_polyline_intersections
from ..geometry.soilpolygon import SoilPolygon
from ..geometry.soillayer import SoilLayer
from ..soil.soil import Soil as LLSoil

load_dotenv()
DSTABILITY_MIGRATION_CONSOLE_PATH = os.getenv("DSTABILITY_MIGRATION_CONSOLE_PATH")


class MaterialLayoutType(IntEnum):
    CLAY_EMBANKEMENT_ON_CLAY = 10
    SAND_EMBANKEMENT_ON_CLAY = 11
    CLAY_EMBANKEMENT_ON_SAND = 12
    SAND_EMBANKEMENT_ON_SAND = 13


class DStability(BaseModel):
    name: str = ""
    characteristic_points: List[CharacteristicPoint] = []
    model: DStabilityModel = DStabilityModel()
    current_scenario_index: int = 0
    current_stage_index: int = 0
    soillayers: List[Dict] = []
    soils: Dict = {}
    headlines: List[Dict] = []
    result: Dict = {}
    points: List[Tuple[float, float]] = []
    boundary: List[Tuple[float, float]] = []
    surface: List[Tuple[float, float]] = []
    waternet_settings: Dict = {}

    @classmethod
    def from_soilprofile1(
        self,
        soilprofile1: SoilProfile1,
    ) -> "DStability":
        pass

    @classmethod
    def from_soilprofileN(
        self,
        soilprofileN: SoilProfileN,
        crosssection_points: List[Tuple[float, float]] = [],
        fill_material_top="clay",
        fill_material_bottom="sand",
    ) -> "DStability":

        soilcollection = soilprofileN.soilcollection
        spgs = soilprofileN.to_soilpolygons(
            crosssection_points=crosssection_points,
            fill_material_top=fill_material_top,
            fill_material_bottom=fill_material_bottom,
        )

        return DStability.from_soilpolygons(spgs, soilcollection)

    @classmethod
    def from_soilpolygons(
        cls,
        soilpolygons: List[SoilPolygon],
        soilcollection: SoilCollection,
        old_ds: "DStability" = None,
    ) -> "DStability":
        ds = DStability()

        # create soils and remember ids
        soil_ids = {}
        # TODO > de volgende lijn moet beter.. zou in de constructor moeten komen van de DStability class
        soilcodes_in_ds = [s.Code for s in ds.model.soils.Soils]
        for soil in soilcollection.soils:
            if soil.code in soilcodes_in_ds:
                continue
            soil_id = ds.model.add_soil(
                Soil(
                    code=soil.code,
                    color="#FF" + soil.color[1:],
                    soil_weight_parameters=SoilWeightParameters(
                        saturated_weight=soil.y_sat, unsaturated_weight=soil.y_dry
                    ),
                    mohr_coulomb_parameters=MohrCoulombParameters(
                        cohesion=soil.cohesion,
                        dilatancy_angle=soil.cohesion,
                        friction_angle=soil.friction_angle,
                    ),
                    shear_strength_model_above_phreatic_level="Mohr_Coulomb",
                    shear_strength_model_below_phreatic_level="Mohr_Coulomb",
                    name=soil.code,
                )
            )
            soil_ids[soil.code] = soil_id

        for spg in soilpolygons:
            ds.model.add_layer(
                label=spg.soilcode,
                points=[Point(x=p[0], z=p[1]) for p in spg.points],
                soil_code=spg.soilcode,
            )

        if old_ds is not None:
            ws = old_ds.model.datastructure.waternetcreatorsettings[0]
            id = ds.model.datastructure.waternetcreatorsettings[0].Id
            ds.model.datastructure.waternetcreatorsettings[0] = ws
            ds.model.datastructure.waternetcreatorsettings[0].Id = id

        return ds

    @classmethod
    def from_stix(cls, stix_file: str, auto_upgrade=True) -> "DStability":
        """Generate a DStability object from a stix file

        Args:
            stix_file (str): The stix file path

        Returns:
            DStability: A DStability object
        """
        result = DStability()
        result.name = Path(stix_file).stem
        try:
            result.model.parse(Path(stix_file))
        except ValueError as e:
            if str(e) == "Can't listdir a file" and auto_upgrade:
                try:
                    subprocess.run(
                        [DSTABILITY_MIGRATION_CONSOLE_PATH, stix_file, stix_file]
                    )
                    result.model.parse(Path(stix_file))
                except Exception as e:
                    raise e
            else:
                raise e

        result.set_scenario_and_stage(0, 0)
        result._post_process()
        return result

    @property
    def left(self) -> float:
        """Get the left x coordinate of the current geometry

        Returns:
            float: The left x coordinate of the current geometry
        """
        return min([p[0] for p in self.points])

    @property
    def right(self) -> float:
        """Get the right x coordinate of the current geometry

        Returns:
            float: The right x coordinate of the current geometry
        """
        return max([p[0] for p in self.points])

    @property
    def top(self) -> float:
        """Get the top z coordinate of the current geometry

        Returns:
            float: The top z coordinate of the current geometry
        """
        return max([p[1] for p in self.points])

    @property
    def bottom(self) -> float:
        """Get the bottom z coordinate of the current geometry

        Returns:
            float: The bottom z coordinate of the current geometry
        """
        return min([p[1] for p in self.points])

    @property
    def phreatic_line(self) -> Optional[PersistableHeadLine]:
        """Get the phreatic line object

        Returns:
            Optional[PersistableHeadLine]: The preathic line or None if not set
        """
        waternet = self.model.waternets[
            0
        ]  # [0] is that correct? don't think so! should depend on the current geom
        for headline in waternet.HeadLines:
            if headline.Id == waternet.PhreaticLineId:
                return headline

        return None

    @property
    def has_phreatic_line(self):
        return self.phreatic_line is not None

    @property
    def phreatic_line_points(self) -> List[Tuple[float, float]]:
        """Get the points of the current phreatic line

        Raises:
            ValueError: Raises an error if no phreatic line is found

        Returns:
            List[Tuple[float, float]]: The points of the phreatic line (x,z)
        """
        pl = self.phreatic_line
        if pl is not None:
            return [(float(p.X), float(p.Z)) for p in self.phreatic_line.Points]
        else:
            return []

    @property
    def soilpolygons(self) -> List[SoilPolygon]:
        return [
            SoilPolygon(points=sl["points"], soilcode=sl["soil"]["code"])
            for sl in self.soillayers
        ]

    @property
    def soilcollection(self) -> SoilCollection:
        sc = SoilCollection()

        for soil in self.soils:
            sc.add(
                LLSoil(
                    code=soil["code"],
                    color=soil["color"],
                    y_dry=soil["yd"],
                    y_sat=soil["ys"],
                    cohesion=soil["cohesion"],
                    friction_angle=soil["friction_angle"],
                )
            )
        return sc

    @property
    def ditch_points(self) -> List[Tuple[float, float]]:
        """Get the ditch points from left (riverside) to right (landside), this will return
        the ditch embankement side, ditch embankement side bottom, land side bottom, land side
        or empty list if there are not ditch points

        Returns:
            List[Tuple[float, float]]: List of points or empty list if no ditch is found
        """

        p1 = self.get_characteristic_point(
            CharacteristicPointType.DITCH_EMBANKEMENT_SIDE
        )
        p2 = self.get_characteristic_point(
            CharacteristicPointType.DITCH_BOTTOM_EMBANKEMENT_SIDE
        )
        p3 = self.get_characteristic_point(
            CharacteristicPointType.DITCH_BOTTOM_LAND_SIDE
        )
        p4 = self.get_characteristic_point(CharacteristicPointType.DITCH_LAND_SIDE)

        if p1.is_valid and p2.is_valid and p3.is_valid and p4.is_valid:
            return [
                (p1.x, self.z_at(p1.x)),
                (p2.x, self.z_at(p1.x)),
                (p3.x, self.z_at(p1.x)),
                (p4.x, self.z_at(p1.x)),
            ]
        else:
            return []

    @property
    def has_ditch(self) -> bool:
        """Returns if the model has assigned ditch points

        Returns:
            bool: True if there is a ditch, False otherwise
        """
        return len(self.ditch_points) == 4

    def get_closest_point_from_x(self, x: float) -> Tuple[float, float]:
        """Get the closest point to the given x coordinate

        Args:
            x (float): The x coordinate

        Returns:
            Tuple[float, float]: The x and z coordinate of the closest point
        """
        result, dlmin = None, 1e9

        for p in self.surface:
            dl = abs(p[0] - x)
            if dl < dlmin:
                result = p
                dlmin = dl

        return result

    def add_layer(
        self,
        points: List[Tuple[float, float]],
        soil_code: str,
        label: str = "",
        notes: str = "",
        scenario_index: Optional[int] = None,
        stage_index: Optional[int] = None,
    ) -> int:
        self.model.add_layer(
            [Point(x=p[0], z=p[1]) for p in points],
            soil_code,
            label,
            notes,
            scenario_index,
            stage_index,
        )
        self._post_process()

    def get_characteristic_point(
        self, point_type: CharacteristicPointType
    ) -> CharacteristicPoint:
        # karakteristieke punten
        wns = self.model.datastructure.waternetcreatorsettings[0]

        if point_type == CharacteristicPointType.EMBANKEMENT_TOE_WATER_SIDE:
            if wns.EmbankmentCharacteristics.EmbankmentToeWaterSide is not "NaN":
                return CharacteristicPoint(
                    x=float(wns.EmbankmentCharacteristics.EmbankmentToeWaterSide),
                    point_type=CharacteristicPointType.EMBANKEMENT_TOE_WATER_SIDE,
                )
            else:
                return CharacteristicPoint(
                    x=nan,
                    point_type=CharacteristicPointType.EMBANKEMENT_TOE_WATER_SIDE,
                )
        elif point_type == CharacteristicPointType.EMBANKEMENT_TOP_WATER_SIDE:
            if wns.EmbankmentCharacteristics.EmbankmentTopWaterSide is not "NaN":
                return CharacteristicPoint(
                    x=float(wns.EmbankmentCharacteristics.EmbankmentTopWaterSide),
                    point_type=CharacteristicPointType.EMBANKEMENT_TOP_WATER_SIDE,
                )
            else:
                return CharacteristicPoint(
                    x=nan,
                    point_type=CharacteristicPointType.EMBANKEMENT_TOP_WATER_SIDE,
                )
        elif point_type == CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE:
            if wns.EmbankmentCharacteristics.EmbankmentTopLandSide is not "NaN":
                return CharacteristicPoint(
                    x=float(wns.EmbankmentCharacteristics.EmbankmentTopLandSide),
                    point_type=CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE,
                )
            else:
                return CharacteristicPoint(
                    x=nan,
                    point_type=CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE,
                )

        elif point_type == CharacteristicPointType.SHOULDER_BASE_LAND_SIDE:
            if wns.EmbankmentCharacteristics.ShoulderBaseLandSide is not "NaN":
                return CharacteristicPoint(
                    x=float(wns.EmbankmentCharacteristics.ShoulderBaseLandSide),
                    point_type=CharacteristicPointType.SHOULDER_BASE_LAND_SIDE,
                )
            else:
                return CharacteristicPoint(
                    x=nan,
                    point_type=CharacteristicPointType.SHOULDER_BASE_LAND_SIDE,
                )
        elif point_type == CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE:
            if wns.EmbankmentCharacteristics.EmbankmentToeLandSide is not "NaN":

                return CharacteristicPoint(
                    x=float(wns.EmbankmentCharacteristics.EmbankmentToeLandSide),
                    point_type=CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE,
                )
            else:
                return CharacteristicPoint(
                    x=nan,
                    point_type=CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE,
                )
        elif point_type == CharacteristicPointType.DITCH_EMBANKEMENT_SIDE:
            if wns.DitchCharacteristics.DitchEmbankmentSide is not "NaN":
                return CharacteristicPoint(
                    x=float(wns.DitchCharacteristics.DitchEmbankmentSide),
                    point_type=CharacteristicPointType.DITCH_EMBANKEMENT_SIDE,
                )
            else:
                return CharacteristicPoint(
                    x=nan,
                    point_type=CharacteristicPointType.DITCH_EMBANKEMENT_SIDE,
                )
        elif point_type == CharacteristicPointType.DITCH_BOTTOM_EMBANKEMENT_SIDE:
            if wns.DitchCharacteristics.DitchBottomEmbankmentSide is not "NaN":
                return CharacteristicPoint(
                    x=float(wns.DitchCharacteristics.DitchBottomEmbankmentSide),
                    point_type=CharacteristicPointType.DITCH_BOTTOM_EMBANKEMENT_SIDE,
                )
            else:
                return CharacteristicPoint(
                    x=nan,
                    point_type=CharacteristicPointType.DITCH_BOTTOM_EMBANKEMENT_SIDE,
                )
        elif point_type == CharacteristicPointType.DITCH_BOTTOM_LAND_SIDE:
            if wns.DitchCharacteristics.DitchBottomLandSide is not "NaN":
                return CharacteristicPoint(
                    x=float(wns.DitchCharacteristics.DitchBottomLandSide),
                    point_type=CharacteristicPointType.DITCH_BOTTOM_LAND_SIDE,
                )
            else:
                return CharacteristicPoint(
                    x=nan,
                    point_type=CharacteristicPointType.DITCH_BOTTOM_LAND_SIDE,
                )
        elif point_type == CharacteristicPointType.DITCH_LAND_SIDE:
            if wns.DitchCharacteristics.DitchLandSide is not "NaN":
                return CharacteristicPoint(
                    x=float(wns.DitchCharacteristics.DitchLandSide),
                    point_type=CharacteristicPointType.DITCH_LAND_SIDE,
                )
            else:
                return CharacteristicPoint(
                    x=nan,
                    point_type=CharacteristicPointType.DITCH_LAND_SIDE,
                )

        else:
            raise ValueError(
                f"Invalid characteristic point type ({point_type}) requested"
            )

    def get_headline_by_label(self, label: str = "") -> PersistableHeadLine:
        for hl in self.model.waternets[0].HeadLines:
            if hl.Label == label:
                return hl
        raise ValueError(f"No headline with label '{label}' in this model.")

    def get_headline_coordinates(self, label: str) -> List[Tuple[float, float]]:
        """Get the coordinates of the given headline

        Args:
            label (str): The label of the headline

        Returns:
            List[Tuple[float, float]]: List of points of the given headline
        """
        for hl in self.model.waternets[0].HeadLines:
            if hl.Label == label:
                return [(float(p.X), float(p.Z)) for p in hl.Points]

        raise ValueError(f"Invalid headline label '{label}' (not found)")

    def set_headline_coordinates(self, label: str, coords: List[Tuple[float, float]]):
        """Overwrite the current coordinates (from left to right) of a headline with the given coordinates

        Args:
            label (str): Label of the headline
            coords (List[Tuple[float, float]]): New coordinates
        """
        for hl in self.model.waternets[0].HeadLines:
            if hl.Label == label:
                if len(coords) > len(hl.Points):
                    raise ValueError(
                        f"Trying to set more coords ({len(coords)}) then currently in headline '{label}' ({len(hl.Points)})"
                    )
                for i in range(len(coords)):
                    hl.Points[i] = PersistablePoint(X=coords[i][0], Z=coords[i][1])
                self._post_process()
                return

        raise ValueError(f"Invalid headline label '{label}' (not found)")

    @property
    def remarks(self) -> str:
        if self.model.datastructure.projectinfo.Remarks is None:
            return ""
        else:
            return self.model.datastructure.projectinfo.Remarks

    @property
    def num_scenarios(self) -> int:
        return len(self.model.scenarios)

    def num_stages(self, scenario_index: int) -> int:
        if scenario_index < len(self.model.scenarios):
            return len(self.model.scenarios[scenario_index].Stages)
        else:
            raise ValueError(f"Invalid scenario index {scenario_index}")

    def stage_label(self, scenario_index: int, stage_index: int) -> str:
        if scenario_index < len(self.model.scenarios):
            if stage_index < len(self.model.scenarios[scenario_index].Stages):
                return self.model.scenarios[scenario_index].Stages[stage_index].Label
            else:
                raise ValueError(f"Invalid stage index {stage_index}")
        else:
            raise ValueError(f"Invalid scenario index {scenario_index}")

    def scenario_label(self, scenario_index: int) -> str:
        if scenario_index < len(self.model.scenarios):
            return self.model.scenarios[0].Label
        raise ValueError(f"Invalid scenario index {scenario_index}")

    def set_phreatic_line(self, points: List[Tuple[float, float]]):
        """Set the phreatic line from the given points

        Args:
            points (List[Tuple[float, float]]): A list of points
        """
        # TODO this is still far from ideal because it leave the old
        # pl line. That has no influence on the result but it looks bad

        # 1. check if we already have a phreatic line
        if self.has_phreatic_line:
            points = [PersistablePoint(X=p[0], Z=p[1]) for p in points]
            for i, hl in enumerate(self.model.datastructure.waternets[0].HeadLines):
                if hl.Id == self.model.datastructure.waternets[0].PhreaticLineId:
                    self.model.datastructure.waternets[0].HeadLines[i].Points = points
                    break
        else:
            self.model.add_head_line(
                [Point(x=p[0], z=p[1]) for p in points],
                "Phreatic line",
                is_phreatic_line=True,
                scenario_index=self.current_scenario_index,
                stage_index=self.current_stage_index,
            )
        self._post_process()

    def _post_process(self):
        """Do some post processing stuff to set properties and save time"""
        # get the points
        layers = self.model._get_geometry(
            self.current_scenario_index, self.current_stage_index
        ).Layers
        polygons = []
        self.points = []

        self.soillayers = []
        self.soils = {}
        self.points = []
        self.boundary = []
        self.surface = []

        soilcolors = {
            sv.SoilId: sv.Color[:1] + sv.Color[3:]  # remove the alpha part
            for sv in self.model.datastructure.soilvisualizations.SoilVisualizations
        }

        for soil in self.model.soils.Soils:
            if not soil.Id in soilcolors.keys():
                color = "#54575c"
            else:
                color = soilcolors[soil.Id]
            self.soils[soil.Id] = {
                "code": soil.Code,
                "name": soil.Name,
                "color": color,
                "yd": soil.VolumetricWeightAbovePhreaticLevel,
                "ys": soil.VolumetricWeightBelowPhreaticLevel,
                "cohesion": 0.0,
                "friction_angle": 0.0,
            }
            if (
                soil.ShearStrengthModelTypeAbovePhreaticLevel
                == ShearStrengthModelTypePhreaticLevelInternal.MOHR_COULOMB_CLASSIC
                and soil.ShearStrengthModelTypeAbovePhreaticLevel
                == soil.ShearStrengthModelTypeAbovePhreaticLevel
            ):
                self.soils[soil.Id][
                    "cohesion"
                ] = soil.MohrCoulombClassicShearStrengthModel.Cohesion
                self.soils[soil.Id][
                    "friction_angle"
                ] = soil.MohrCoulombClassicShearStrengthModel.FrictionAngle
            if (
                soil.ShearStrengthModelTypeAbovePhreaticLevel
                == ShearStrengthModelTypePhreaticLevelInternal.MOHR_COULOMB_ADVANCED
                and soil.ShearStrengthModelTypeAbovePhreaticLevel
                == soil.ShearStrengthModelTypeAbovePhreaticLevel
            ):
                self.soils[soil.Id][
                    "cohesion"
                ] = soil.MohrCoulombAdvancedShearStrengthModel.Cohesion
                self.soils[soil.Id][
                    "friction_angle"
                ] = soil.MohrCoulombAdvancedShearStrengthModel.FrictionAngle

        soillayers = {}
        for sl in self.model.datastructure.soillayers[0].SoilLayers:
            soillayers[sl.LayerId] = sl.SoilId

        for layer in layers:
            self.points += [(float(p.X), float(p.Z)) for p in layer.Points]
            polygons.append(Polygon([(float(p.X), float(p.Z)) for p in layer.Points]))
            self.soillayers.append(
                {
                    "points": [(float(p.X), float(p.Z)) for p in layer.Points],
                    "soil": self.soils[soillayers[layer.Id]],
                    "layer_id": layer.Id,
                }
            )

        # now remove the ids of the soils
        self.soils = [d for d in self.soils.values()]

        # get the surface
        # merge all polygons and return the boundary of that polygon
        boundary = orient(unary_union(polygons), sign=-1)

        # get the points
        self.boundary = [
            (round(p[0], 3), round(p[1], 3))
            for p in list(zip(*boundary.exterior.coords.xy))[:-1]
        ]

        # get the leftmost point
        left = min([p[0] for p in self.boundary])
        topleft_point = sorted(
            [p for p in self.boundary if p[0] == left], key=lambda x: x[1]
        )[-1]

        # get the rightmost points
        right = max([p[0] for p in self.boundary])
        rightmost_point = sorted(
            [p for p in self.boundary if p[0] == right], key=lambda x: x[1]
        )[-1]

        # get the index of leftmost point
        idx_left = self.boundary.index(topleft_point)
        self.surface = self.boundary[idx_left:] + self.boundary[:idx_left]

        # get the index of the rightmost point
        idx_right = self.surface.index(rightmost_point)
        self.surface = self.surface[: idx_right + 1]

        # headlines
        for hl in self.model.waternets[0].HeadLines:
            self.headlines.append(
                {
                    "label": hl.Label,
                    "points": [(p.X, p.Z) for p in hl.Points],
                    "is_phreatic": hl.Id == self.model.waternets[0].PhreaticLineId,
                }
            )

    def get_soil_from_layer_id(self, layer_id: str):
        for sl in self.soillayers:
            if sl["layer_id"] == layer_id:
                return sl["soil"]
        return None

    def surface_intersections(
        self, polyline: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        return polyline_polyline_intersections(polyline, self.surface)

    def surface_points_between(
        self, left: float, right: float
    ) -> List[Tuple[float, float]]:
        """Get a list of surface points between the given limits

        Args:
            left (float): The left limit
            right (float): The right limit

        Returns:
            List[Tuple[float, float]]: List of surface points between left and right
        """
        return [p for p in self.surface if p[0] > left and p[0] < right]

    def set_scenario_and_stage(self, scenario_index: int, stage_index: int):
        """Set the current scenario and stage

        Args:
            scenario_index (int): The scenario index
            stage_index (int): The stage index

        Raises:
            ValueError: Raises an error if the scenario index or stage index is / are invalid
        """
        if scenario_index < len(self.model.scenarios):
            self.current_scenario_index = scenario_index
        else:
            raise ValueError(f"Trying to set an invalid scenario index")

        if stage_index < len(self.model.scenarios[self.current_scenario_index].Stages):
            self.current_stage_index = stage_index
        else:
            raise ValueError(
                f"Trying to set an invalid stage index for scenario {self.current_scenario_index}"
            )

    def soilprofile1_at(
        self, x: float, scenario_index: int = 0, stage_index: int = 0
    ) -> SoilProfile1:
        """Generate a SoilProfile1 at the given x coordinate

        Args:
            x (float): the location to create the SoilProfile1
            scenario_index (int, optional): _description_. Defaults to 0.
            stage_index (int, optional): _description_. Defaults to 0.

        Returns:
            SoilProfile1: The soilprofile1, the bottom layer will always end at -999.0
        """
        result = SoilProfile1()

        layers = self.model._get_geometry(scenario_index, stage_index).Layers

        soillayers = []

        for layer in layers:
            points = [(float(p.X), float(p.Z)) for p in layer.Points]
            points.append(points[0])
            for i in range(1, len(points)):
                p1 = points[i - 1]
                if i == len(points):
                    p2 = points[0]
                else:
                    p2 = points[i]

                if min(p1[0], p2[0]) <= x and x <= max(p1[0], p2[0]):
                    soil = self.get_soil_from_layer_id(layer.Id)
                    if p1[0] == p2[0]:
                        z = round(p1[1], 3)
                    else:
                        z = round(
                            p1[1] + (x - p1[0]) / (p2[0] - p1[0]) * (p2[1] - p1[1]), 3
                        )
                    soillayers.append((z, soil))

        soillayers = sorted(soillayers, key=lambda x: x[0], reverse=True)
        if soillayers[0] == soillayers[1]:
            soillayers = soillayers[1:]
        result = SoilProfile1(
            soillayers=[
                SoilLayer(
                    top=soillayers[0][0], bottom=0.0, soilcode=soillayers[0][1]["code"]
                )
            ]
        )

        for i in range(1, int(len(soillayers) / 2)):
            option1 = soillayers[i * 2 - 1]
            option2 = soillayers[i * 2]

            if option1[1]["code"] == result.soillayers[-1].soilcode:
                result.soillayers[-1].bottom = option1[0]
                add_layer = option2
            else:
                result.soillayers[-1].bottom = option2[0]
                add_layer = option1

            result.soillayers.append(
                SoilLayer(top=add_layer[0], bottom=0.0, soilcode=add_layer[1]["code"])
            )
        result.soillayers[-1].bottom = -999.0
        return result

    def z_at(self, x, scenario_index: int = 0, stage_index: int = 0) -> List[float]:
        """Get a list of z coordinates from intersections with the soillayers on coordinate x

        Args:
            x (_type_): The x coordinate
            scenario_index (int, optional): The scenario index. Defaults to 0.
            stage_index (int, optional): The stage index. Defaults to 0.

        Returns:
            List[float]: A list of intersections sorted from high to low
        """
        sp1 = self.soilprofile1_at(x, scenario_index, stage_index)
        return [sl.top for sl in sp1.soillayers]

    def has_soilcode(self, soilcode: str) -> bool:
        """Check if the current model has the given soilcode

        Args:
            soilcode (str): The soilcode to check for

        Returns:
            bool: True if the soilcode is available
        """
        return soilcode in [d["code"] for d in self.soils]

    def serialize(self, location: Union[FilePath, DirectoryPath, BinaryIO]):
        """Serialize the model to a file

        Args:
            location (Union[FilePath, DirectoryPath, BinaryIO]): The path to save to
        """
        self.model.serialize(location)

    def execute(self):
        self.model = self.model.execute()

    def extract_soilparameters(self) -> List[str]:
        result = [
            "name,code,model,yd,ys,probabilistic,cohesion,friction angle,dilatancy,S,m\n"
        ]
        for soil in self.model.soils.Soils:
            d = {
                "name": soil.Name,
                "code": soil.Code,
                "model": "",
                "yd": f"{soil.VolumetricWeightAbovePhreaticLevel:.2f}",
                "ys": f"{soil.VolumetricWeightBelowPhreaticLevel:.2f}",
                "prob": "",
                "c": "",
                "phi": "",
                "dilatancy": "",
                "S": "",
                "m": "",
            }

            if soil.IsProbabilistic:
                d["prob"] = "true"
            else:
                ssma = soil.ShearStrengthModelTypeAbovePhreaticLevel
                ssmb = soil.ShearStrengthModelTypeBelowPhreaticLevel

                if (
                    ssma
                    == ShearStrengthModelTypePhreaticLevelInternal.MOHR_COULOMB_ADVANCED
                ):
                    d["model"] = "MOHR_COULOMB_ADVANCED"
                    d["c"] = (
                        f"{soil.MohrCoulombAdvancedShearStrengthModel.Cohesion:.2f}"
                    )
                    d["phi"] = (
                        f"{soil.MohrCoulombAdvancedShearStrengthModel.FrictionAngle:.2f}"
                    )
                    d["dilatancy"] = (
                        f"{soil.MohrCoulombAdvancedShearStrengthModel.Dilatancy:.2f}"
                    )
                elif (
                    ssma
                    == ShearStrengthModelTypePhreaticLevelInternal.MOHR_COULOMB_CLASSIC
                ):
                    d["model"] = "MOHR_COULOMB_CLASSIC"
                    d["c"] = f"{soil.MohrCoulombClassicShearStrengthModel.Cohesion:.2f}"
                    d["phi"] = (
                        f"{soil.MohrCoulombClassicShearStrengthModel.FrictionAngle:.2f}"
                    )
                elif ssma == ShearStrengthModelTypePhreaticLevelInternal.NONE:
                    d["model"] = "NONE"
                elif ssma == ShearStrengthModelTypePhreaticLevelInternal.SU:
                    d["model"] = "SU"
                    d["S"] = f"{soil.SuShearStrengthModel.ShearStrengthRatio:.2f}"
                    d["m"] = f"{soil.SuShearStrengthModel.StrengthIncreaseExponent:.2f}"
                elif ssma == ShearStrengthModelTypePhreaticLevelInternal.SUTABLE:
                    d["model"] = "SUTABLE"
            result.append(
                f"{d['name']},{d['code']},{d['model']},{d['yd']},{d['ys']},{d['prob']},{d['c']},{d['phi']},{d['dilatancy']},{d['S']},{d['m']}\n"
            )
        return result

    def get_analysis_type(
        self, scenario_index: int = 0, stage_index: int = 0
    ) -> AnalysisTypeEnum:
        cs = self.model._get_calculation_settings(scenario_index, stage_index)
        return cs.AnalysisType

    def safety_factor_to_dict(self, scenario_index: int = 0, stage_index: int = 0):
        try:
            sf = self.model.get_result(scenario_index, stage_index)
        except Exception as e:
            return {}

        if type(sf) == UpliftVanParticleSwarmResult:
            return {
                "model": "upliftvan_particle_swarm",
                "fos": sf.FactorOfSafety,
                "left_circle": {
                    "x": sf.LeftCenter.X,
                    "z": sf.LeftCenter.Z,
                },
                "right_circle": {
                    "x": sf.RightCenter.X,
                    "z": sf.RightCenter.Z,
                },
                "tangent": sf.TangentLine,
            }
        elif type(sf) == BishopBruteForceResult:
            return {
                "model": "bishop_brute_force",
                "fos": sf.FactorOfSafety,
                "circle": {
                    "x": sf.Circle.Center.X,
                    "z": sf.Circle.Center.Z,
                    "r": sf.Circle.Radius,
                },
            }
        elif type(sf) == SpencerGeneticAlgorithmResult:
            return {
                "model": "spencer_genetic_algorithm",
                "fos": sf.FactorOfSafety,
                "slip_plane": [{"x": p.X, "z": p.Z} for p in sf.SlipPlane],
            }
        else:
            raise ValueError(
                f"Cannot convert the result of type '{type(sf) }' yet, for now limited to spencer genetic, bishop brute force, uplift particlr swarm"
            )
