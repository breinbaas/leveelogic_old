from leveelogic.deltares.dstability import DStability
from leveelogic.deltares.runner import Runner


class TestDeltaresRunner:
    def test_runner(self):
        dma = DStability.from_stix("tests/testdata/stix/complex_geometry.stix")
        dmb = DStability.from_stix("tests/testdata/stix/fc_pl_sample.stix")
        dmc = DStability.from_stix("tests/testdata/stix/real_sample.stix")

        runner = Runner(models=[dma, dmb, dmc])
        runner.execute()
