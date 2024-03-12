from typing import List, Tuple
from copy import deepcopy
from shapely.geometry import Polygon, MultiPolygon
from ...geolib.models.dstability.internal import (
    AnalysisTypeEnum,
    PersistableSearchGrid,
    NullablePersistablePoint,
    PersistableTangentLines,
    PersistableSlipPlaneConstraints,
)

from .algorithm import Algorithm, AlgorithmInputCheckError
from ..dstability import DStability
from ...geometry.characteristic_point import CharacteristicPointType


DEFAULT_TANGENT_HEIGHT = 5.0


class AlgorithmAddCalculationSettings(Algorithm):

    bbf_bottomleft: Tuple[float, float] = None
    bbf_height: float = None
    bbf_width: float = None
    bbf_tangent_top: float = None
    bbf_tangent_height: float = None
    bbf_space: float = 1.0
    bbf_tangent_space: float = 0.5
    bbf_min_circle_depth: float = 2.0
    bbf_min_slipplane_length: float = 2.0

    def _check_input(self):
        if not self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "The given stix file has no embankment top land side point (see waternet creator settings) which is required for this algorithm to run."
            )

        if not self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "The given stix file has no embankment toe land side point (see waternet creator settings) which is required for this algorithm to run."
            )

        return True

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        # the result depends on the calculation method
        if ds.get_analysis_type() == AnalysisTypeEnum.BISHOP_BRUTE_FORCE:
            # guess values if they are not given
            x_top_landside = self.ds.get_characteristic_point(
                CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE
            ).x
            x_toe_landside = self.ds.get_characteristic_point(
                CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
            ).x
            z_top_landside = self.ds.z_at(x_top_landside)[0]
            z_toe_landside = self.ds.z_at(x_toe_landside)[0]
            if self.bbf_height is None:
                self.bbf_height = x_toe_landside - x_top_landside
            if self.bbf_width is None:
                self.bbf_width = x_toe_landside - x_top_landside
            if self.bbf_bottomleft is None:
                self.bbf_bottomleft = (
                    x_top_landside,
                    z_top_landside + 1.0,
                )
            if self.bbf_tangent_top is None:
                self.bbf_tangent_top = z_toe_landside
            if self.bbf_tangent_height is None:
                self.bbf_tangent_height = DEFAULT_TANGENT_HEIGHT

            # set the calculation settings
            # Grid
            ds.model.datastructure.calculationsettings[
                0
            ].BishopBruteForce.SearchGrid = PersistableSearchGrid(
                BottomLeft=NullablePersistablePoint(
                    X=self.bbf_bottomleft[0], Z=self.bbf_bottomleft[1]
                ),
                Label="added by leveelogic algorithm",
                NumberOfPointsInX=int(self.bbf_width / self.bbf_space),
                NumberOfPointsInZ=int(self.bbf_height / self.bbf_space),
                Space=self.bbf_space,
            )
            # Tangent lines
            ds.model.datastructure.calculationsettings[
                0
            ].BishopBruteForce.TangentLines = PersistableTangentLines(
                BottomTangentLineZ=z_toe_landside - 1.0 - self.bbf_tangent_height,
                Label="added by leveelogic algorithm",
                NumberOfTangentLines=int(
                    self.bbf_tangent_height / self.bbf_tangent_space
                ),
                Space=self.bbf_tangent_space,
            )
            # Constraints
            if (
                self.bbf_min_circle_depth == 0.0
                and self.bbf_min_slipplane_length == 0.0
            ):
                ds.model.datastructure.calculationsettings[
                    0
                ].BishopBruteForce.SlipPlaneConstraints = PersistableSlipPlaneConstraints(
                    IsSizeConstraintsEnabled=False,
                    MinimumSlipPlaneDepth=0.0,
                    MinimumSlipPlaneLength=0.0,
                )
            else:
                ds.model.datastructure.calculationsettings[
                    0
                ].BishopBruteForce.SlipPlaneConstraints = PersistableSlipPlaneConstraints(
                    IsSizeConstraintsEnabled=True,
                    MinimumSlipPlaneDepth=self.bbf_min_circle_depth,
                    MinimumSlipPlaneLength=self.bbf_min_slipplane_length,
                )
        elif ds.get_analysis_type() == AnalysisTypeEnum.SPENCER_GENETIC:
            raise NotImplementedError(
                f"This calculation method is not YET implemented in this algorithm"
            )
        elif ds.get_analysis_type() == AnalysisTypeEnum.UPLIFT_VAN_PARTICLE_SWARM:
            raise NotImplementedError(
                f"This calculation method is not YET implemented in this algorithm"
            )
        else:
            raise NotImplementedError(
                f"This calculation method is not implemented in this algorithm"
            )

        return ds
