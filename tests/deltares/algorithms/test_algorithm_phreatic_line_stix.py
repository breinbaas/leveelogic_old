from leveelogic.deltares.algorithms.algorithm_phreatic_line_stix import (
    AlgorithmPhreaticLineStix,
)
from leveelogic.deltares.dstability import DStability


class TestAlgorithmPhreaticLineStix:
    def test_clay_on_sand(self):
        ds = DStability.from_stix("tests/testdata/stix/clay_on_sand.stix")
        alg = AlgorithmPhreaticLineStix(ds=ds, river_level=3.0, polder_level=-0.5)
        ds = alg.execute()
        ds.serialize("tests/testdata/output/clay_on_sand_phreatic_line.stix")
