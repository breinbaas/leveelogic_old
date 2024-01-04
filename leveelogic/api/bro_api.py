from pydantic import BaseModel
from urllib.request import urlopen
import requests
import xmltodict
import random

from .bro_objects import CPTCharacteristics, Envelope, Point
from ..soilinvestigation.cpt import Cpt, CptReadError
from ..settings import BRO_CPT_DOWNLOAD_URL, BRO_CPT_CHARACTERISTICS_URL


class BROAPI(BaseModel):
    def _get_cpt_metadata_by_bounds(
        self,
        left: float,
        top: float,
        right: float,
        bottom: float,
        max_num: int = -1,
    ):
        envelope = Envelope(
            lower_corner=Point(lat=left, lon=bottom),
            upper_corner=Point(lat=right, lon=top),
        )

        headers = {
            "accept": "application/xml",
            "Content-Type": "application/json",
        }

        json = {"area": envelope.bro_json}

        response = requests.post(
            BRO_CPT_CHARACTERISTICS_URL, headers=headers, json=json, timeout=10
        )

        available_cpt_objects = []

        # TODO: Check status codes in BRO REST API documentation.
        if response.status_code == 200:
            parsed = xmltodict.parse(
                response.content, attr_prefix="", cdata_key="value"
            )
            rejection_reason = parsed["dispatchCharacteristicsResponse"].get(
                "brocom:rejectionReason"
            )
            if rejection_reason:
                raise ValueError(f"{rejection_reason}")

            nr_of_documents = parsed["dispatchCharacteristicsResponse"].get(
                "numberOfDocuments"
            )
            if nr_of_documents is None or nr_of_documents == "0":
                raise ValueError(
                    "No available objects have been found in given date + area range. Retry with different parameters."
                )

            for document in parsed["dispatchCharacteristicsResponse"][
                "dispatchDocument"
            ]:
                # TODO: Hard skip, this is likely to happen when it's deregistered. document will have key ["BRO_DO"]["brocom:deregistered"] = "ja"
                # TODO: Add this information to logger
                if "CPT_C" not in document.keys():
                    continue
                available_cpt_objects.append(CPTCharacteristics(document["CPT_C"]))

                if max_num != -1 and len(available_cpt_objects) > max_num:
                    available_cpt_objects = random.choices(
                        available_cpt_objects, k=max_num
                    )

            return available_cpt_objects

        response.raise_for_status()

    def _get_cpt_from_bro_id(self, bro_id):
        URL = f"{BRO_CPT_DOWNLOAD_URL}/{bro_id}"
        try:
            s = urlopen(URL).read()
            return Cpt.from_string(s, suffix=".xml")
        except Exception as e:
            raise CptReadError(
                f"Error reading cpt file from url '{URL}', got error '{e}' "
            )

    def get_cpts_by_bounds(
        self,
        left: float,
        right: float,
        top: float,
        bottom: float,
        max_num: int = -1,
    ):
        cpt_characteristics = self._get_cpt_metadata_by_bounds(
            left=left, top=top, right=right, bottom=bottom, max_num=1
        )

        cpts = [self._get_cpt_from_bro_id(cc.bro_id) for cc in cpt_characteristics]

        return cpts
