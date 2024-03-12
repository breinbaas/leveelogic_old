from pydantic import BaseModel
from pathlib import Path
from typing import List, Dict, Tuple
from shapely.geometry import Polygon

from ..geolib.models.dgeoflow import DGeoFlowModel


class DGeoFlow(BaseModel):
    name: str = ""
    model: DGeoFlowModel = DGeoFlowModel()
    current_scenario_index: int = 0
    current_stage_index: int = 0
    soillayers: List[Dict] = []
    soils: Dict = {}
    # result: Dict = {}
    points: List[Tuple[float, float]] = []
    boundary: List[Tuple[float, float]] = []
    surface: List[Tuple[float, float]] = []
    boundary_conditions: List[Dict] = []

    @classmethod
    def from_flox(cls, flox_file: str) -> "DGeoFlow":
        """Generate a DGeoFlow object from a flox file

        Args:
            flox_file (str): The flox file path

        Returns:
            DStability: A DStability object
        """
        result = DGeoFlow()
        result.name = Path(flox_file).stem
        try:
            result.model.parse(Path(flox_file))
        except Exception as e:
            raise ValueError(f"Could not parse file '{flox_file}', got error '{e}'")

        result._post_process()

        return result

    def _post_process(self):
        layers = self.model.datastructure.geometries[0].Layers
        polygons = []
        points = []

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
            self.soils[soil.Id] = {
                "code": soil.Code,
                "name": soil.Name,
                "color": soilcolors[soil.Id],
                "k_hor": soil.HorizontalPermeability,
                "k_ver": soil.VerticalPermeability,
            }

        soillayers = {}
        for sl in self.model.datastructure.soillayers[0].SoilLayers:
            soillayers[sl.LayerId] = sl.SoilId

        for layer in layers:
            points += layer.Points
            polygons.append(Polygon([(p.X, p.Z) for p in layer.Points]))
            self.soillayers.append(
                {
                    "points": [(p.X, p.Z) for p in layer.Points],
                    "soil": self.soils[soillayers[layer.Id]],
                }
            )

        self.points = [(p.X, p.Z) for p in points]

        # now remove the ids of the soils
        self.soils = [d for d in self.soils.values()]

        # boundary conditions
        for bc in self.model.datastructure.boundary_conditions[0].BoundaryConditions:
            self.boundary_conditions.append(
                {
                    "label": bc.Label,
                    "head_level": bc.FixedHeadBoundaryConditionProperties.HeadLevel,
                    "points": [(p.X, p.Z) for p in bc.Points],
                }
            )
