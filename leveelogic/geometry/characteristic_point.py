from enum import IntEnum

from ..models.datamodel import DataModel


class CharacteristicPointType(IntEnum):
    NONE = 0

    START_SURFACE = 10  # maaiveld buitenwaarts
    END_SURFACE = 11  # maaiveld binnenwaarts

    REFERENCE_POINT = 20
    TOE_LEFT = 21
    CREST_LEFT = 22
    CREST_RIGHT = 23
    TOE_RIGHT = 24

    START_ROAD = 30
    END_ROAD = 31

    START_POLDER = 40

    START_DITCH = 50
    END_DITCH = 51


CharacteristicPointNames = {
    CharacteristicPointType.NONE: "none",
    CharacteristicPointType.START_SURFACE: "start surface",
    CharacteristicPointType.END_SURFACE: "end surface",
    CharacteristicPointType.REFERENCE_POINT: "reference point",
    CharacteristicPointType.TOE_LEFT: "toe left",
    CharacteristicPointType.CREST_LEFT: "crest left",
    CharacteristicPointType.CREST_RIGHT: "crest right",
    CharacteristicPointType.TOE_RIGHT: "toe right",
    CharacteristicPointType.START_ROAD: "start road",
    CharacteristicPointType.END_ROAD: "end road",
    CharacteristicPointType.START_POLDER: "start polder",
    CharacteristicPointType.START_DITCH: "start ditch",
    CharacteristicPointType.END_DITCH: "end ditch",
}


class CharacteristicPoint(DataModel):
    """Class to store characteristic point information"""

    x: float
    point_type: CharacteristicPointType
