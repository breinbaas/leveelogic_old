from typing import List, Tuple
from copy import deepcopy
from geolib.geometry.one import Point
import numpy as np

from .algorithm import Algorithm
from ..dstability import DStability
from ...calculations.functions import sf_to_beta


class AlgorithmFC(Algorithm):
    """This algorithm will calculate a fragility curve based on the phreatic line

    Args:
        river level: float, waterlevel in the river


    Returns:
        Dict: dictionary with keys 'waterlevel' and 'safetyfactor'
    """

    max_level: float
    min_level: float
    step: float
    dz: float

    log: List[str] = []

    def _check_input(self):
        pass

    def _execute(self) -> DStability:
        result = {"waterlevel": [], "fos": [], "reliability_index": []}
        ds = deepcopy(self.ds)

        for z in np.arange(self.min_level, self.max_level + self.step * 0.5, self.step):
            surface_intersections = ds.surface_intersections(
                [(ds.left, z), (ds.right, z)]
            )

            if len(surface_intersections) == 0:
                continue

            ds.phreatic_line.Points[0] = Point(x=ds.left, z=z)
            ds.phreatic_line.Points[1] = Point(x=surface_intersections[0][0], z=z)
            ds.phreatic_line.Points[2] = Point(
                x=surface_intersections[0][0], z=z - self.dz
            )

            old_coords = ds.get_headline_coordinates("Stijghoogtelijn 3 (PL3)")
            ds.set_headline_coordinates(
                "Stijghoogtelijn 3 (PL3)", [(ds.left, z), (old_coords[1][0], z)]
            )

            ds.serialize(f"tests/testdata/output/fc_pl_sample_{z:.2f}.stix")
            try:
                ds.model.execute()
                sfdict = ds.safety_factor_to_dict()
                result["waterlevel"].append(z)
                result["fos"].append(sfdict["fos"])
                result["reliability_index"].append(
                    sf_to_beta(sfdict["fos"], model_factor=1.06)
                )
            except Exception as e:
                self.log.append(f"Error at z={z:.2f}, error: '{e}'")

        return result
