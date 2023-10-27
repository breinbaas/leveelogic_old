from leveelogic.deltares.algorithms.algorithm_berm import AlgorithmBerm
from leveelogic.deltares.dstability import DStability


class TestAlgorithmBerm:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmBerm(
            ds=ds,
            soilcode="H_Rk_ko",
            x_toe=25,
            slope_top=10,
            slope_bottom=1,
            initial_height=2.0,
            initial_width=6.0,
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/simple_geometry_berm.stix")
