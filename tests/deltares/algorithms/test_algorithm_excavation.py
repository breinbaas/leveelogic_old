from leveelogic.deltares.algorithms.algorithm_excavation import AlgorithmExcavation
from leveelogic.deltares.dstability import DStability


class TestAlgorithmExcavation:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmExcavation(ds=ds, x=25.0, width=4.0, depth=1.5)
        ds = alg.execute()
        ds.serialize("tests/testdata/output/simple_geometry_excavation.stix")
