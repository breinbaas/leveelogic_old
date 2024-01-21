from pyproj import Transformer
from pydantic import BaseModel
from typing import Optional


def _str2bool(s) -> bool:
    """
    converts a value to bool based on certain
    :param s: int, str, float
    :return: bool
    """
    return str(s).lower() in ("ja", "yes", "true", "t", "1")


class Point(BaseModel):
    lat: float
    lon: float

    def from_wgs84_to_rd(self) -> "RDPoint":
        transformer = Transformer.from_crs(4326, 28992)
        rd_y, rd_x = transformer.transform(self.lat, self.lon)
        return RDPoint(rd_y, rd_x)


class RDPoint(BaseModel):
    x: float
    y: float

    def from_rd_to_wgs84(self) -> "Point":
        transformer = Transformer.from_crs(28992, 4326)
        lat, lon = transformer.transform(self.x, self.y)
        return Point(lat, lon)


class Envelope(BaseModel):
    lower_corner: Point
    upper_corner: Point

    @property
    def bro_json(self):
        return {
            "boundingBox": {
                "lowerCorner": {
                    "lat": self.lower_corner.lat,
                    "lon": self.lower_corner.lon,
                },
                "upperCorner": {
                    "lat": self.upper_corner.lat,
                    "lon": self.upper_corner.lon,
                },
            }
        }

    @property
    def to_geojson_feature(self) -> dict:
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [self.lower_corner.lon, self.lower_corner.lat],
                        [self.upper_corner.lon, self.lower_corner.lat],
                        [self.upper_corner.lon, self.upper_corner.lat],
                        [self.lower_corner.lon, self.upper_corner.lat],
                        [self.lower_corner.lon, self.lower_corner.lat],
                    ]
                ],
            },
            "properties": {"description": "Requested area"},
        }


class CPTCharacteristics:
    """
    Class to save all Characteristics of a CPT object, resulting from a characteristics search on the API
    """

    def __init__(self, parsed_dispatch_document: dict):
        self.gml_id: str = parsed_dispatch_document["gml:id"]
        self.bro_id: str = parsed_dispatch_document["brocom:broId"]
        self.deregistered: bool = _str2bool(
            parsed_dispatch_document["brocom:deregistered"]
        )
        self.accountable_party: int = parsed_dispatch_document[
            "brocom:deliveryAccountableParty"
        ]
        self.quality_regime: str = parsed_dispatch_document["brocom:qualityRegime"]
        self.object_registration_time: str = parsed_dispatch_document[
            "brocom:objectRegistrationTime"
        ]
        self.under_review: bool = _str2bool(
            parsed_dispatch_document["brocom:underReview"]
        )
        xy = parsed_dispatch_document["brocom:standardizedLocation"]["gml:pos"].split(
            " "
        )
        self.standardized_location: Point = Point(lat=float(xy[0]), lon=float(xy[1]))
        xy = parsed_dispatch_document["brocom:deliveredLocation"]["gml:pos"].split(" ")
        self.delivered_location: RDPoint = RDPoint(x=float(xy[0]), y=float(xy[1]))
        self.local_vertical_reference_point: Optional[str] = (
            parsed_dispatch_document["localVerticalReferencePoint"]["value"]
            if parsed_dispatch_document.get("localVerticalReferencePoint")
            else None
        )
        self.vertical_datum: Optional[str] = (
            parsed_dispatch_document["verticalDatum"]["value"]
            if parsed_dispatch_document.get("verticalDatum")
            else None
        )
        self.cpt_standard: Optional[str] = (
            parsed_dispatch_document["cptStandard"]["value"]
            if parsed_dispatch_document.get("cptStandard")
            else None
        )
        self.offset: Optional[float] = (
            float(parsed_dispatch_document["offset"]["value"])
            if parsed_dispatch_document.get("offset")
            else None
        )
        self.quality_class: Optional[str] = (
            parsed_dispatch_document["qualityClass"]["value"]
            if parsed_dispatch_document.get("qualityClass")
            else None
        )
        self.research_report_date: Optional[str] = (
            parsed_dispatch_document["researchReportDate"]["brocom:date"]
            if parsed_dispatch_document.get("researchReportDate")
            else None
        )
        self.start_time: Optional[str] = parsed_dispatch_document.get("startTime")
        self.predrilled_depth: Optional[float] = (
            float(parsed_dispatch_document["predrilledDepth"]["value"])
            if parsed_dispatch_document.get("predrilledDepth")
            else None
        )
        self.final_depth: Optional[float] = (
            float(parsed_dispatch_document["finalDepth"]["value"])
            if parsed_dispatch_document.get("finalDepth")
            else None
        )
        self.survey_purpose: Optional[str] = (
            parsed_dispatch_document["surveyPurpose"]["value"]
            if parsed_dispatch_document.get("surveyPurpose")
            else None
        )
        self.dissipation_test_performed: Optional[bool] = (
            _str2bool(parsed_dispatch_document["dissipationTestPerformed"])
            if parsed_dispatch_document.get("dissipationTestPerformed")
            else None
        )
        self.stop_criterion: Optional[str] = (
            parsed_dispatch_document["stopCriterion"]["value"]
            if parsed_dispatch_document.get("stopCriterion")
            else None
        )

    @property
    def to_geojson_feature(self) -> dict:
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.wgs84_coordinate.lon, self.wgs84_coordinate.lat],
            },
            "properties": {"bro_id": f"{self.bro_id}"},
        }

    @property
    def rd_coordinate(self) -> RDPoint:
        return self.delivered_location

    @property
    def wgs84_coordinate(self) -> Point:
        return self.standardized_location

    @property
    def total_cpt_length(self) -> Optional[float]:
        if isinstance(self.offset, float) and isinstance(self.final_depth, float):
            return round(self.offset + self.final_depth, 2)
        return None
