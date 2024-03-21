from leveelogic.deltares.algorithms.algorithm_fc_phreatic_line_wsbd import (
    AlgorithmFCPhreaticLineWSBD,
)
from leveelogic.deltares.dstability import DStability


class TestAlgorithmFCPhreaticLineWSBD:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_alg_pl_wsbd.stix")
        alg = AlgorithmFCPhreaticLineWSBD(ds=ds, min_level=2.0, max_level=5.0, step=0.5)
        result = alg.execute_multiple_results()

        for i, ds in enumerate(result):
            ds.serialize(f"tests/testdata/output/fc_phreatic_line_wsbd_{i}.stix")

        assert len(result) == 7

    def test_sand_on_clay(self):
        ds = DStability.from_stix("tests/testdata/stix/sand_on_clay.stix")
        alg = AlgorithmFCPhreaticLineWSBD(ds=ds, min_level=5.0, max_level=6.0, step=1.0)
        result = alg.execute_multiple_results()
        for i, ds in enumerate(result):
            ds.serialize(f"tests/testdata/output/sand_on_clay_{i}.stix")
