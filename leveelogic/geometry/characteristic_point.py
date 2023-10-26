from enum import IntEnum

from ..models.datamodel import DataModel


class CharacteristicPointType(IntEnum):
    NONE = 0

    START_RIVER = 10
    END_RIVER = 11

    REFERENCE_POINT = 20
    CREST_LEFT_BOTTOM = 21
    CREST_LEFT_TOP = 22
    CREST_RIGHT_TOP = 23
    CREST_RIGHT_BOTTOM = 24

    START_ROAD = 30
    END_ROAD = 31

    START_POLDER = 40

    START_DITCH = 50
    END_DITCH = 51


CharacteristicPointNames = {
    CharacteristicPointType.NONE: "none",
    CharacteristicPointType.START_RIVER: "start river",
    CharacteristicPointType.END_RIVER: "end river",
    CharacteristicPointType.REFERENCE_POINT: "reference point",
    CharacteristicPointType.CREST_LEFT_BOTTOM: "crest left bottom",
    CharacteristicPointType.CREST_LEFT_TOP: "crest left top",
    CharacteristicPointType.CREST_RIGHT_TOP: "crest right top",
    CharacteristicPointType.CREST_RIGHT_BOTTOM: "crest right bottom",
    CharacteristicPointType.START_ROAD: "start road",
    CharacteristicPointType.END_ROAD: "end road",
    CharacteristicPointType.START_POLDER: "start polder",
    CharacteristicPointType.START_DITCH: "start ditch",
    CharacteristicPointType.END_DITCH: "end ditch",
}


class CharacteristicPoint(DataModel):
    """Class to store characteristic point information"""

    l: float
    point_type: CharacteristicPointType = CharacteristicPointType.NONE
