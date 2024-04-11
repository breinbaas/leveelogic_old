from leveelogic.deltares.algorithms.algorithm_phreatic_line import (
    AlgorithmPhreaticLine,
)
from leveelogic.deltares.dstability import DStability
import matplotlib.pyplot as plt


class TestAlgorithmPhreaticLineStix:

    def test_clay_on_clay(self):
        ds = DStability.from_stix("tests/testdata/stix/pl_clay_on_clay.stix")
        ds_solution = DStability.from_stix(
            "tests/testdata/stix/solutions/pl_clay_on_clay_solution.stix"
        )
        pts_old = ds_solution.phreatic_line_points
        alg = AlgorithmPhreaticLine(ds=ds, river_level=18, polder_level=8)
        ds = alg.execute()
        pts_new = ds.phreatic_line_points
        plt.figure(figsize=(15, 5))
        plt.plot(
            [p[0] for p in pts_old], [p[1] for p in pts_old], "b--", label="solution"
        )
        plt.plot(
            [p[0] for p in pts_new], [p[1] for p in pts_new], "k-", label="algorithm"
        )
        plt.legend()
        plt.savefig("tests/testdata/output/test_pl_clay_on_clay.png")
        ds.serialize("tests/testdata/output/test_pl_clay_on_clay.stix")

    def test_clay_on_sand(self):
        ds = DStability.from_stix("tests/testdata/stix/pl_clay_on_sand.stix")
        ds_solution = DStability.from_stix(
            "tests/testdata/stix/solutions/pl_clay_on_sand_solution.stix"
        )
        pts_old = ds_solution.phreatic_line_points
        alg = AlgorithmPhreaticLine(ds=ds, river_level=18, polder_level=8)
        ds = alg.execute()
        pts_new = ds.phreatic_line_points
        plt.figure(figsize=(15, 5))
        plt.plot(
            [p[0] for p in pts_old], [p[1] for p in pts_old], "b--", label="solution"
        )
        plt.plot(
            [p[0] for p in pts_new], [p[1] for p in pts_new], "k-", label="algorithm"
        )
        plt.legend()
        plt.savefig("tests/testdata/output/test_pl_clay_on_sand.png")
        ds.serialize("tests/testdata/output/test_pl_clay_on_sand.stix")

    def test_sand_on_clay(self):
        ds = DStability.from_stix("tests/testdata/stix/pl_sand_on_clay.stix")
        ds_solution = DStability.from_stix(
            "tests/testdata/stix/solutions/pl_sand_on_clay_solution.stix"
        )
        pts_old = ds_solution.phreatic_line_points
        alg = AlgorithmPhreaticLine(ds=ds, river_level=18, polder_level=8)
        ds = alg.execute()
        pts_new = ds.phreatic_line_points
        plt.figure(figsize=(15, 5))
        plt.plot(
            [p[0] for p in pts_old], [p[1] for p in pts_old], "b--", label="solution"
        )
        plt.plot(
            [p[0] for p in pts_new], [p[1] for p in pts_new], "k-", label="algorithm"
        )
        plt.legend()
        plt.savefig("tests/testdata/output/test_pl_sand_on_clay.png")
        ds.serialize("tests/testdata/output/test_pl_sand_on_clay.stix")

    def test_sand_on_sand(self):
        ds = DStability.from_stix("tests/testdata/stix/pl_sand_on_sand.stix")
        ds_solution = DStability.from_stix(
            "tests/testdata/stix/solutions/pl_sand_on_sand_solution.stix"
        )
        pts_old = ds_solution.phreatic_line_points
        alg = AlgorithmPhreaticLine(ds=ds, river_level=18, polder_level=8)
        ds = alg.execute()
        pts_new = ds.phreatic_line_points
        plt.figure(figsize=(15, 5))
        plt.plot(
            [p[0] for p in pts_old], [p[1] for p in pts_old], "b--", label="solution"
        )
        plt.plot(
            [p[0] for p in pts_new], [p[1] for p in pts_new], "k-", label="algorithm"
        )
        plt.legend()
        plt.savefig("tests/testdata/output/test_pl_sand_on_sand.png")
        ds.serialize("tests/testdata/output/test_pl_sand_on_sand.stix")
