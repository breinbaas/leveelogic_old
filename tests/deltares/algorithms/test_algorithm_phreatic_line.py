from leveelogic.deltares.algorithms.algorithm_phreatic_line import (
    AlgorithmPhreaticLine,
)
from leveelogic.deltares.dstability import DStability


class TestAlgorithmPhreaticLineStix:
    # def test_clay_on_sand(self):
    #     ds = DStability.from_stix("tests/testdata/stix/clay_on_sand.stix")
    #     alg = AlgorithmPhreaticLine(ds=ds, river_level=3.0, polder_level=-0.5)
    #     ds = alg.execute()
    #     ds.serialize("tests/testdata/output/clay_on_sand_phreatic_line.stix")

    # def test_sand_on_clay(self):
    #     ds = DStability.from_stix("tests/testdata/stix/sand_on_clay.stix")
    #     alg = AlgorithmPhreaticLine(
    #         ds=ds, river_level=5.0, polder_level=-1.5, surface_offset=0.1
    #     )
    #     ds = alg.execute()
    #     ds.serialize("tests/testdata/output/sand_on_clay_phreatic_line.stix")

    def test_clay_on_clay(self):
        ds = DStability.from_stix("tests/testdata/stix/pl_clay_on_clay.stix")
        alg = AlgorithmPhreaticLine(ds=ds, river_level=18, polder_level=8)
        ds = alg.execute()
        ds.serialize("tests/testdata/output/test_pl_clay_on_clay.stix")

    def test_clay_on_sand(self):
        ds = DStability.from_stix("tests/testdata/stix/pl_clay_on_sand.stix")
        alg = AlgorithmPhreaticLine(ds=ds, river_level=18, polder_level=8)
        ds = alg.execute()
        ds.serialize("tests/testdata/output/test_pl_clay_on_sand.stix")

    def test_sand_on_clay(self):
        ds = DStability.from_stix("tests/testdata/stix/pl_sand_on_clay.stix")
        alg = AlgorithmPhreaticLine(ds=ds, river_level=18, polder_level=8)
        ds = alg.execute()
        ds.serialize("tests/testdata/output/test_pl_sand_on_clay.stix")

    def test_sand_on_sand(self):
        ds = DStability.from_stix("tests/testdata/stix/pl_sand_on_sand.stix")
        alg = AlgorithmPhreaticLine(ds=ds, river_level=18, polder_level=8)
        ds = alg.execute()
        ds.serialize("tests/testdata/output/test_pl_sand_on_sand.stix")
