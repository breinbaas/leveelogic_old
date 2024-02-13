from enum import IntEnum
from math import isnan

from ..models.datamodel import DataModel


class CharacteristicPointType(IntEnum):
    NONE = 0

    EMBANKEMENT_TOE_WATER_SIDE = 10
    EMBANKEMENT_TOP_WATER_SIDE = 11
    EMBANKEMENT_TOP_LAND_SIDE = 12
    SHOULDER_BASE_LAND_SIDE = 13
    EMBANKEMENT_TOE_LAND_SIDE = 14
    DITCH_EMBANKEMENT_SIDE = 15
    DITCH_BOTTOM_EMBANKEMENT_SIDE = 16
    DITCH_BOTTOM_LAND_SIDE = 17
    DITCH_LAND_SIDE = 18


CharacteristicPointNames = {
    CharacteristicPointType.NONE: "none",
    CharacteristicPointType.EMBANKEMENT_TOE_WATER_SIDE: "embankement toe water side",
    CharacteristicPointType.EMBANKEMENT_TOP_WATER_SIDE: "embankement top water side",
    CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE: "embankement top land side",
    CharacteristicPointType.SHOULDER_BASE_LAND_SIDE: "shoulder base land side",
    CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE: "embankement toe land side",
    CharacteristicPointType.DITCH_EMBANKEMENT_SIDE: "ditch embankement side",
    CharacteristicPointType.DITCH_BOTTOM_EMBANKEMENT_SIDE: "ditch bottom embankement side",
    CharacteristicPointType.DITCH_BOTTOM_LAND_SIDE: "ditch land side",
    CharacteristicPointType.DITCH_LAND_SIDE: "ditch land side",
}


class CharacteristicPoint(DataModel):
    """Class to store characteristic point information"""

    x: float
    point_type: CharacteristicPointType

    @property
    def is_valid(self) -> bool:
        return not isnan(self.x)
