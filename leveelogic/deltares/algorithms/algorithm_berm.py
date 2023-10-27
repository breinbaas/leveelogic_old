from ..dstability import DStability
from copy import deepcopy

from .algorithm import Algorithm


class AlgorithmBerm(Algorithm):
    soilcode: str
    x_toe: float
    slope_top: float
    slope_bottom: float
    initial_width: float
    initial_height: float

    def _check_input(self):
        # do we have this soilcode
        if not self.ds.has_soilcode(self.soilcode):
            raise ValueError(f"AlgorithmBerm got an invalid soilcode '{self.soilcode}'")

        # do we have a valid x coordinate

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        return ds
