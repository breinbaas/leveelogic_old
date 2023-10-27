from leveelogic.deltares.algorithms.algorithm_berm import AlgorithmBerm
from leveelogic.deltares.dstability import DStability
from leveelogic.geometry.characteristic_point import CharacteristicPointType


class TestAlgorithmBerm:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        ds.set_characteristic_point(25, point_type=CharacteristicPointType.TOE_RIGHT)
        alg = AlgorithmBerm(
            ds=ds,
            soilcode="H_Rk_ko",
            slope_top=10,
            slope_bottom=1,
            initial_height=2.0,
            initial_width=6.0,
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/simple_geometry_berm.stix")
