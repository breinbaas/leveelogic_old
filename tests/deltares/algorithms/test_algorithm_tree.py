from leveelogic.deltares.algorithms.algorithm_tree import AlgorithmTree
from leveelogic.deltares.dstability import DStability


class TestAlgorithmTree:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmTree(
            ds=ds,
            x=20.0,
            tree_height=10.0,
            width_of_root_zone=6.0,
            load=10.0,
            wind_force=15.0,
            angle_of_distribution=30,
        )
        ds = alg.execute()

        ds.set_scenario_and_stage(1, 0)
        alg.ds = ds  # update the model
        alg.x = 25.0
        ds = alg.execute()

        ds.serialize("tests/testdata/output/simple_geometry_tree.stix")
