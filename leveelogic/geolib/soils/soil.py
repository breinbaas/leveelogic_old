from enum import Enum, IntEnum
from math import isfinite
from typing import List, Optional, Union

from pydantic import validator

from ..geometry.one import Point
from ..models import BaseDataClass

from .soil_utils import Color


class SoilBaseModel(BaseDataClass):
    @validator("*")
    def fail_on_infinite(cls, v, values, field):
        if isinstance(v, float) and not isfinite(v):
            raise ValueError(
                "Only finite values are supported, don't use nan, -inf or inf."
            )
        return v


class DistributionType(IntEnum):
    Undefined = 0
    Normal = 2
    LogNormal = 3
    Deterministic = 4


class StochasticParameter(SoilBaseModel):
    """
    Stochastic parameters class
    """

    is_probabilistic: bool = False
    mean: Optional[float] = None
    standard_deviation: Optional[float] = 0
    distribution_type: Optional[DistributionType] = DistributionType.Normal
    correlation_coefficient: Optional[float] = None
    low_characteristic_value: Optional[float] = None
    high_characteristic_value: Optional[float] = None
    low_design_value: Optional[float] = None
    high_design_value: Optional[float] = None


class ShearStrengthModelTypePhreaticLevel(Enum):
    """
    Shear Strength Model Type. These types represent the
    shear strength model that can be found in the UI of
    the D-Stability program.
    """

    MOHR_COULOMB = "Mohr_Coulomb"
    NONE = "None"
    SHANSEP = "SHANSEP"
    SUTABLE = "SuTable"

    def transform_shear_strength_model_type_to_internal(self):
        from ..models.dstability.internal import (
            ShearStrengthModelTypePhreaticLevelInternal,
        )

        transformation_dict = {
            "Mohr_Coulomb": ShearStrengthModelTypePhreaticLevelInternal.MOHR_COULOMB_ADVANCED,
            "None": ShearStrengthModelTypePhreaticLevelInternal.NONE,
            "SHANSEP": ShearStrengthModelTypePhreaticLevelInternal.SU,
            "SuTable": ShearStrengthModelTypePhreaticLevelInternal.SUTABLE,
        }
        return transformation_dict[self.value]


class MohrCoulombParameters(SoilBaseModel):
    """
    Mohr Coulomb parameters class
    """

    cohesion: Optional[Union[float, StochasticParameter]] = StochasticParameter()
    dilatancy_angle: Optional[Union[float, StochasticParameter]] = StochasticParameter()
    friction_angle: Optional[Union[float, StochasticParameter]] = StochasticParameter()
    friction_angle_interface: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    is_delta_angle_automatically_calculated: Optional[bool] = None
    cohesion_and_friction_angle_correlated: Optional[bool] = None


class SuTablePoint(SoilBaseModel):
    su: float = None
    stress: float = None


class UndrainedParameters(SoilBaseModel):
    """
    Undrained shear strength parameters class. This class includes the SU Table and SHANSEP model variables included in D-Stability.
    """

    shear_strength_ratio: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    shear_strength_ratio_and_shear_strength_exponent_correlated: Optional[bool] = None
    strength_increase_exponent: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    s_and_m_correlated: Optional[bool] = None
    undrained_shear_strength: Optional[float] = None
    undrained_shear_strength_top: Optional[float] = None
    undrained_shear_strength_bottom: Optional[float] = None
    undrained_shear_strength_bearing_capacity_factor: Optional[float] = None
    su_table: Optional[List[SuTablePoint]] = None
    probabilistic_su_table: Optional[bool] = None
    su_table_variation_coefficient: Optional[float] = None

    def to_su_table_points(self):
        from ..models.dstability.internal import PersistableSuTablePoint

        su_table = None
        if self.su_table is not None:
            su_table = []
            for su_point in self.su_table:
                su_table.append(
                    PersistableSuTablePoint(
                        EffectiveStress=su_point.stress, Su=su_point.su
                    )
                )
        return su_table


class BjerrumParameters(SoilBaseModel):
    """
    Bjerrum parameters class

    input_type_is_comp_ratio: [bool] is true when compression input mode is "compression ratio", false when compression
                                     input mode is "Compression index"
    If input_type_is_comp_ratio is true, the following parameters are used as input:
            reloading_swelling_RR
            compression_ratio_CR
            coef_secondary_compression_Ca

    If input_type_is_comp_ratio is false, the following parameters are used as input:
            reloading_swelling_index_Cr
            compression_index_Cc
            coef_secondary_compression_Ca
    """

    input_type_is_comp_ratio: Optional[bool] = None
    reloading_ratio: Optional[Union[float, StochasticParameter]] = StochasticParameter()
    primary_compression_ratio: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    correlation_reload_primary_compression_ratio: Optional[float] = None
    reloading_index: Optional[Union[float, StochasticParameter]] = StochasticParameter()
    primary_compression_index: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    coef_secondary_compression_Ca: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    reloading_swelling_RR: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    compression_ratio_CR: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    reloading_swelling_index_Cr: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    compression_index_Cc: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )


class StateType(Enum):
    POP = "POP"
    OCR = "OCR"
    YIELD_STRESS = "yield_stress"


class IsotacheParameters(SoilBaseModel):
    precon_isotache_type: Optional[StateType] = None
    reloading_swelling_constant_a: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )  # SoilStdPriCompIndex
    primary_compression_constant_b: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )  # SoilStdSecCompIndex
    secondary_compression_constant_c: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )  # SoilStdSecCompRate


class KoppejanParameters(SoilBaseModel):
    precon_koppejan_type: Optional[StateType] = None
    preconsolidation_pressure: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    soil_ap_as_approximation_by_Cp_Cs: Optional[bool] = False
    primary_Cp: Optional[Union[float, StochasticParameter]] = StochasticParameter()
    primary_Cp_point: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    secular_Cs: Optional[Union[float, StochasticParameter]] = StochasticParameter()
    secular_Cs_point: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    primary_Ap: Optional[Union[float, StochasticParameter]] = StochasticParameter()
    primary_Asec: Optional[Union[float, StochasticParameter]] = StochasticParameter()


class StorageTypes(IntEnum):
    vertical_consolidation_coefficient = 0
    constant_permeability = 1
    strain_dependent_permeability = 2


class StorageParameters(SoilBaseModel):
    """
    In this case vertical_permeability has a unit of [m/day]. In GUI
    of the D-Settlement this value is displayed as [m/s].
    """

    vertical_permeability: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    permeability_horizontal_factor: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    horizontal_permeability: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    storage_type: Optional[StorageTypes]
    permeability_strain_type: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter(mean=1e15)
    )
    vertical_consolidation_coefficient: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )


class SoilWeightParameters(SoilBaseModel):
    saturated_weight: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    unsaturated_weight: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )


class GrainType(IntEnum):
    FINE = 0
    COARSE = 1


class SoilClassificationParameters(SoilBaseModel):
    """
    Soil classification class
    """

    initial_void_ratio: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    min_void_ratio: Optional[float] = None
    max_void_ratio: Optional[float] = None
    porosity: Optional[Union[float, StochasticParameter]] = StochasticParameter()
    relative_density: Optional[float] = None
    d_50: Optional[float] = None
    grain_type: Optional[GrainType] = (
        GrainType.FINE
    )  # TODO this must refer to a intenum class


class SoilStiffnessParameters(SoilBaseModel):
    emod_menard: Optional[float] = None


class ModulusSubgradeReaction(IntEnum):
    MANUAL = 0
    MENARD = 1


class LambdaType(IntEnum):
    MANUAL = 0
    MULLERBRESLAU = 1
    KOTTER = 2


class SubgradeReactionParameters(SoilBaseModel):
    modulus_subgrade_reaction_type: Optional[ModulusSubgradeReaction] = None
    lambda_type: Optional[LambdaType] = None
    tangent_secant_1: Optional[float] = None
    tangent_secant_2: Optional[float] = None
    tangent_secant_3: Optional[float] = None
    k_o_top: Optional[float] = None
    k_1_top: Optional[float] = None
    k_2_top: Optional[float] = None
    k_3_top: Optional[float] = None
    k_4_top: Optional[float] = None
    k_o_bottom: Optional[float] = None
    k_1_bottom: Optional[float] = None
    k_2_bottom: Optional[float] = None
    k_3_bottom: Optional[float] = None
    k_4_bottom: Optional[float] = None
    k_1_top_side: Optional[float] = None
    k_2_top_side: Optional[float] = None
    k_3_top_side: Optional[float] = None
    k_1_bottom_side: Optional[float] = None
    k_2_bottom_side: Optional[float] = None
    k_3_bottom_side: Optional[float] = None


class EarthPressureCoefficientsType(IntEnum):
    MANUAL = 0
    BRINCHHANSEN = 1


class EarthPressureCoefficients(SoilBaseModel):
    earth_pressure_coefficients_type: Optional[EarthPressureCoefficientsType] = (
        EarthPressureCoefficientsType.BRINCHHANSEN
    )
    active: Optional[float] = None
    neutral: Optional[float] = None
    passive: Optional[float] = None


class HorizontalBehaviourType(IntEnum):
    Stiff = 1
    Elastic = 2
    Foundation = 3


class HorizontalBehaviour(SoilBaseModel):
    """
    Horizontal behaviour class
    """

    horizontal_behavior_type: Optional[HorizontalBehaviourType] = None
    soil_elasticity: Optional[float] = None
    soil_default_elasticity: Optional[bool] = None


class ConeResistance(SoilBaseModel):
    """
    Cone resistance class
    """

    max_cone_resistance_type: Optional[Enum] = None
    max_cone_resistance: Optional[float] = None


class StatePoint(SoilBaseModel):
    state_point_id: Optional[str] = None
    state_layer_id: Optional[str] = None
    state_point_type: Optional[StateType] = None
    state_point_is_probabilistic: Optional[bool] = None


class StateLine(SoilBaseModel):
    """
    TODO Decide if we want to keep state in soil class
    TODO decide if we want cross-dependency to geometry class
    """

    state_line_points: Optional[List[Point]]


class SoilState(SoilBaseModel):
    use_equivalent_age: Optional[bool] = None
    equivalent_age: Optional[float] = None
    state_points: Optional[StatePoint] = None
    state_lines: Optional[StateLine] = None

    yield_stress_layer: Optional[Union[float, StochasticParameter]] = (
        StochasticParameter()
    )
    ocr_layer: Optional[Union[float, StochasticParameter]] = StochasticParameter()
    pop_layer: Optional[Union[float, StochasticParameter]] = StochasticParameter()
    secondary_swelling_reduced: Optional[bool] = None
    secondary_swelling_factor: Optional[float] = None
    unloading_stress_ratio: Optional[float] = None


class SoilType(IntEnum):
    GRAVEL = 0
    SAND = 1
    LOAM = 2
    CLAY = 3
    PEAT = 4
    SANDY_LOAM = 5
    TERTCLAY = 6
    CLAYEYSAND = 7


class Soil(SoilBaseModel):
    """Soil Material."""

    id: Optional[str] = None
    name: Optional[str] = None
    code: Optional[str] = None
    color: Color = Color("grey")

    mohr_coulomb_parameters: Optional[MohrCoulombParameters] = MohrCoulombParameters()
    undrained_parameters: Optional[UndrainedParameters] = UndrainedParameters()
    bjerrum_parameters: Optional[BjerrumParameters] = BjerrumParameters()
    isotache_parameters: Optional[IsotacheParameters] = IsotacheParameters()
    koppejan_parameters: Optional[KoppejanParameters] = KoppejanParameters()
    storage_parameters: Optional[StorageParameters] = StorageParameters()
    soil_weight_parameters: Optional[SoilWeightParameters] = SoilWeightParameters()
    soil_classification_parameters: Optional[SoilClassificationParameters] = (
        SoilClassificationParameters()
    )
    soil_stiffness_parameters: Optional[SoilStiffnessParameters] = (
        SoilStiffnessParameters()
    )

    horizontal_behaviour: Optional[HorizontalBehaviour] = HorizontalBehaviour()
    cone_resistance: Optional[ConeResistance] = ConeResistance()
    use_tension: Optional[bool] = None
    use_probabilistic_defaults: Optional[bool] = False
    soil_type_settlement_by_vibrations: Optional[SoilType] = SoilType.SAND
    soil_type_nl: Optional[SoilType] = SoilType.SAND
    soil_state: Optional[SoilState] = SoilState()
    shear_strength_model_above_phreatic_level: Optional[
        ShearStrengthModelTypePhreaticLevel
    ] = None
    shear_strength_model_below_phreatic_level: Optional[
        ShearStrengthModelTypePhreaticLevel
    ] = None
    is_drained: Optional[bool] = None
    is_probabilistic: Optional[bool] = None

    earth_pressure_coefficients: Optional[EarthPressureCoefficients] = (
        EarthPressureCoefficients()
    )
    subgrade_reaction_parameters: Optional[SubgradeReactionParameters] = (
        SubgradeReactionParameters()
    )
    shell_factor: Optional[float] = None

    @staticmethod
    def set_stochastic_parameters(input_class: object):
        """
        Converts float to stochastic parameter, where the mean is set as the input float value
        Args:
            input_class:

        Returns:

        """

        try:
            class_dict = input_class.dict()
        except AttributeError:
            return input_class

        for field in input_class.__fields__:
            parameter = input_class.__fields__[field]
            if isinstance(parameter.default, StochasticParameter):
                if isinstance(class_dict[field], float):
                    setattr(
                        input_class, field, StochasticParameter(mean=class_dict[field])
                    )

        return input_class

    def set_all_stochastic_parameters(self):
        """
        Loop over all fields in soil class, and converts floats to stochastic parameters if necessary

        Returns:

        """
        for field in self.__fields__:
            self.set_stochastic_parameters(self.__getattribute__(field))

    def __transfer_soil_dict_to_model(self, soil_dict, model_soil):
        """
        Transfers items from soil dictionary to model if the item is not None
        Args:
            soil_dict: soil dictionary
            model_soil: internal soil in model

        Returns:

        """
        for key, value in dict(
            soil_dict
        ).items():  # override default values with those of the soil
            if key in dict(model_soil).keys() and value is not None:
                if type(value) is dict:
                    self.__transfer_soil_dict_to_model(value, getattr(model_soil, key))
                else:
                    setattr(model_soil, key, value)
        return model_soil

    def __to_dstability_stochastic_parameter(
        self, stochastic_parameter: StochasticParameter
    ):
        from ..models.dstability.internal import (
            PersistableStochasticParameter as DStabilityStochasticParameter,
        )

        kwargs = {
            "IsProbabilistic": stochastic_parameter.is_probabilistic,
            "Mean": stochastic_parameter.mean,
            "StandardDeviation": stochastic_parameter.standard_deviation,
        }

        return self.__transfer_soil_dict_to_model(
            kwargs, DStabilityStochasticParameter()
        )

    def __to_su_table(self):
        from ..models.dstability.internal import PersistableSuTable

        kwargs = {
            "StrengthIncreaseExponent": self.undrained_parameters.strength_increase_exponent.mean,
            "StrengthIncreaseExponentStochasticParameter": self.__to_dstability_stochastic_parameter(
                stochastic_parameter=self.undrained_parameters.strength_increase_exponent
            ),
            "IsSuTableProbabilistic": self.undrained_parameters.probabilistic_su_table,
            "SuTableVariationCoefficient": self.undrained_parameters.su_table_variation_coefficient,
            "SuTablePoints": self.undrained_parameters.to_su_table_points(),
        }
        return self.__transfer_soil_dict_to_model(kwargs, PersistableSuTable())

    def _to_dstability(self):
        from ..models.dstability.internal import PersistableSoil as DStabilitySoil

        self.set_all_stochastic_parameters()

        if self.shear_strength_model_above_phreatic_level is not None:
            shear_strength_model_above_phreatic_level = (
                self.shear_strength_model_above_phreatic_level.transform_shear_strength_model_type_to_internal()
            )
        else:
            shear_strength_model_above_phreatic_level = (
                self.shear_strength_model_above_phreatic_level
            )
        if self.shear_strength_model_below_phreatic_level is not None:
            shear_strength_model_below_phreatic_level = (
                self.shear_strength_model_below_phreatic_level.transform_shear_strength_model_type_to_internal()
            )
        else:
            shear_strength_model_below_phreatic_level = (
                self.shear_strength_model_below_phreatic_level
            )

        kwargs = {
            "Id": self.id,
            "Name": self.name,
            "Code": self.code,
            "MohrCoulombAdvancedShearStrengthModel": {
                "Cohesion": self.mohr_coulomb_parameters.cohesion.mean,
                "CohesionStochasticParameter": self.__to_dstability_stochastic_parameter(
                    self.mohr_coulomb_parameters.cohesion
                ),
                "FrictionAngle": self.mohr_coulomb_parameters.friction_angle.mean,
                "FrictionAngleStochasticParameter": self.__to_dstability_stochastic_parameter(
                    self.mohr_coulomb_parameters.friction_angle
                ),
                "CohesionAndFrictionAngleCorrelated": self.mohr_coulomb_parameters.cohesion_and_friction_angle_correlated,
                "Dilatancy": self.mohr_coulomb_parameters.dilatancy_angle.mean,
                "DilatancyStochasticParameter": self.__to_dstability_stochastic_parameter(
                    self.mohr_coulomb_parameters.dilatancy_angle
                ),
            },
            "SuShearStrengthModel": {
                "ShearStrengthRatio": self.undrained_parameters.shear_strength_ratio.mean,
                "ShearStrengthRatioStochasticParameter": self.__to_dstability_stochastic_parameter(
                    self.undrained_parameters.shear_strength_ratio
                ),
                "StrengthIncreaseExponent": self.undrained_parameters.strength_increase_exponent.mean,
                "StrengthIncreaseExponentStochasticParameter": self.__to_dstability_stochastic_parameter(
                    self.undrained_parameters.strength_increase_exponent
                ),
                "ShearStrengthRatioAndShearStrengthExponentCorrelated": self.undrained_parameters.shear_strength_ratio_and_shear_strength_exponent_correlated,
            },
            "VolumetricWeightAbovePhreaticLevel": self.soil_weight_parameters.unsaturated_weight.mean,
            "VolumetricWeightBelowPhreaticLevel": self.soil_weight_parameters.saturated_weight.mean,
            "IsProbabilistic": self.is_probabilistic,
            "ShearStrengthModelTypeAbovePhreaticLevel": shear_strength_model_above_phreatic_level,
            "ShearStrengthModelTypeBelowPhreaticLevel": shear_strength_model_below_phreatic_level,
            "SuTable": self.__to_su_table(),
        }

        return self.__transfer_soil_dict_to_model(kwargs, DStabilitySoil())

    def _to_dgeoflow(self):
        from ..models.dgeoflow.internal import PersistableSoil as DGeoFlowSoil

        self.set_all_stochastic_parameters()

        kwargs = {
            "Id": self.id,
            "Name": self.name,
            "Code": self.code,
            "HorizontalPermeability": self.storage_parameters.horizontal_permeability.mean,
            "VerticalPermeability": self.storage_parameters.vertical_permeability.mean,
        }
        return self.__transfer_soil_dict_to_model(kwargs, DGeoFlowSoil())
