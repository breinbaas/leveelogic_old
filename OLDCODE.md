### code to remember but not yet added to the library

berm growth

```python
dz = i * self.height_step
dx = dz / ((self.slope_top + self.slope_bottom) / 2.0)
```

algorithm that should not be an algorithm (creates fragility curve plot)
```
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

class TestAlgorithmFC:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_pl_sample.stix")
        alg = AlgorithmFC(ds=ds, min_level=2.0, max_level=4.5, step=0.5, dz=1.44)
        result = alg.execute()

        plt.plot(result["waterlevel"], result["reliability_index"], "o-")
        plt.xlabel("Water level [m]")
        plt.ylabel("Reliability index")
        plt.title("Fragility curve")
        plt.grid()
        plt.savefig("tests/testdata/output/fc_pl_sample.fragility_curve.png")

```

### start of phreatic line

from copy import deepcopy
from typing import List, Tuple
from math import isnan

from ..dstability import DStability
from .algorithm import Algorithm, AlgorithmInputCheckError, AlgorithmExecutionError
from ...helpers import polyline_polyline_intersections
from ...geometry.characteristic_point import CharacteristicPointType


class AlgorithmPhreaticLine(Algorithm):
    waterlevel_river: float
    waterlevel_polder: float
    waterlevel_offset: float = 0.1
    slope: float = 10
    offset_points: List[Tuple[float, float]] = []

    b_offset: float = 1.0
    c_offset: float = 1.5
    d_offset: float = 0.0
    e_offset: float = 0.0

    def _check_input(self):
        if not self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "No point defined for the embankement top land side"
            )
        if not self.ds.get_characteristic_point(
            CharacteristicPointType.SHOULDER_BASE_LAND_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "No point defined for the shoulder base land side"
            )
        if not self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
        ).is_valid:
            raise AlgorithmInputCheckError(
                "No point defined for the embankement toe land side"
            )
        # if not self.ds.get_characteristic_point(
        #     CharacteristicPointType.DITCH_EMBANKEMENT_SIDE
        # ).is_valid:
        #     raise AlgorithmInputCheckError(
        #         "No point defined for the ditch embankement side"
        #     )
        # if not self.ds.get_characteristic_point(
        #     CharacteristicPointType.DITCH_LAND_SIDE
        # ).is_valid:
        #     raise AlgorithmInputCheckError("No point defined for the ditch land side")

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        # PHREATIC LINE POINTS
        # left point
        p1 = (ds.left, self.waterlevel_river)
        river_level_ints = ds.surface_intersections([p1, (ds.right, p1[1])])
        if len(river_level_ints) == 0:
            raise AlgorithmExecutionError(
                "No intersections with the riverlevel and the surface found"
            )

        # [A] Intersection of the river water level with the outerslope
        p2 = river_level_ints[0]
        # [B] River water level minus offset, with default offset 1 m, limited by minimum value
        p3 = (p2[0] + 1.0, self.waterlevel_river - self.b_offset)
        # [C] River water level minus offset, with default offset 1.5 m, limited by minimum value
        p4 = (
            self.ds.get_characteristic_point(
                CharacteristicPointType.EMBANKEMENT_TOP_LAND_SIDE
            ).x,
            self.waterlevel_river - self.c_offset,
        )

        # [E] Surface level at dike toe minus offset, with default offset 0 m.
        cp6x = self.ds.get_characteristic_point(
            CharacteristicPointType.EMBANKEMENT_TOE_LAND_SIDE
        ).x
        p6 = (cp6x, self.ds.z_at(cp6x) - self.e_offset)

        # [D] Linear interpolation between point C and point E, unless the user defines an offset Doffset;user with respect to the surface level
        cp5x = self.ds.get_characteristic_point(
            CharacteristicPointType.SHOULDER_BASE_LAND_SIDE
        ).x
        p5 = (cp5x, 0.0)
        if self.d_offset == 0:
            p5[1] = p4[1] + (p5[0] - p4[0]) * (p6[1] - p4[1]) / (p6[0] - p4[0])
        else:
            p5[1] = self.ds.z_at(cp5x) - self.d_offset

        p8 = (self.ds.right, self.waterlevel_polder)

        # # [F] Intersection point polder level with ditch
        # ditch_intersections = ds.surface_intersections(
        #     [(self.ds.left, self.waterlevel_polder), p8]
        # )

        # xl = ds.get_characteristic_point(
        #     CharacteristicPointType.DITCH_EMBANKEMENT_SIDE
        # ).x
        # xr = self.ds.get_characteristic_point(CharacteristicPointType.DITCH_LAND_SIDE).x

        # ditch_intersections = [
        #     p for p in ditch_intersections if p[0] >= xl and p[0] <= xr
        # ]
        # if len(ditch_intersections) == 0:
        #     raise AlgorithmExecutionError(
        #         "No intersections with the polder level and the ditch found"
        #     )
        # p7 = ditch_intersections[0]

        return ds
