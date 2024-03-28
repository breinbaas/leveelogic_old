from leveelogic.deltares.algorithms.algorithm_excavation import AlgorithmExcavation
from leveelogic.deltares.dstability import DStability


class TestAlgorithmExcavation:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmExcavation(ds=ds, x=25.0, width=4.0, depth=1.5)
        ds = alg.execute()

        ds.set_scenario_and_stage(1, 0)
        alg.ds = ds  # update model
        alg.x = 23.0
        alg.width = 2.0
        alg.depth = 0.5
        ds = alg.execute()

        ds.serialize("tests/testdata/output/simple_geometry_excavation.stix")
