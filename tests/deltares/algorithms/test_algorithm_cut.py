from leveelogic.deltares.algorithms.algorithm_cut import AlgorithmCut
from leveelogic.deltares.dstability import DStability


class TestAlgorithmCut:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmCut(ds=ds, points=[(0, 3), (13, 3), (25, -11), (55, -11)])
        ds = alg.execute()
        ds.serialize("tests/testdata/output/simple_geometry_cut.stix")

    def test_complex_geometry(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_alg_pl_wsbd.stix")
        alg = AlgorithmCut(ds=ds, points=[(-100, 3), (40, -1.5), (130.496, -1.5)])
        ds = alg.execute()
        ds.serialize("tests/testdata/output/fc_alg_pl_wsbd_cut.stix")
