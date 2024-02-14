from leveelogic.deltares.algorithms.algorithm_fill import AlgorithmFill
from leveelogic.deltares.dstability import DStability


class TestAlgorithmFill:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmFill(
            ds=ds, points=[(15, -5), (25, -5), (30, -10)], soilcode="Embankment dry"
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/alg_fill_simple_geometry.stix")

    def test_complex_geometry(self):
        ds = DStability.from_stix("tests/testdata/stix/spikey_geometry.stix")
        alg = AlgorithmFill(
            ds=ds, points=[(25, 12), (50, 12), (55, 5)], soilcode="Embankment dry"
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/alg_fill_spikey_geometry.stix")
