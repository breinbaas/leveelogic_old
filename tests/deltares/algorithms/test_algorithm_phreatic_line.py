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
        pts_old_pl1 = ds_solution.phreatic_line_points
        alg = AlgorithmPhreaticLine(
            ds=ds,
            river_level_mhw=18,
            river_level_ghw=14,
            polder_level=8,
            aquifer_label="L 4",
            hydraulic_head_pl2_inward=10,
            hydraulic_head_pl2_outward=10,
            intrusion_length=1,
            inward_leakage_length_pl3=750,
            outward_leakage_length_pl3=10,
            aquifer_inside_aquitard_label="L 2",
            inward_leakage_length_pl4=400,
            outward_leakage_length_pl4=5,
        )
        ds = alg.execute()
        # pts_new_pl1 = ds.phreatic_line_points
        # plt.figure(figsize=(15, 5))
        # plt.plot(
        #     [p[0] for p in pts_old_pl1],
        #     [p[1] for p in pts_old_pl1],
        #     "b--",
        #     label="PL1 solution",
        # )
        # plt.plot(
        #     [p[0] for p in pts_new_pl1],
        #     [p[1] for p in pts_new_pl1],
        #     "k-",
        #     label="PL1 algorithm",
        # )
        # plt.legend()
        # plt.savefig("tests/testdata/output/test_pl_clay_on_clay.png")
        ds.serialize("tests/testdata/output/test_pl_clay_on_clay.stix")

    def test_clay_on_sand(self):
        ds = DStability.from_stix("tests/testdata/stix/pl_clay_on_sand.stix")
        ds_solution = DStability.from_stix(
            "tests/testdata/stix/solutions/pl_clay_on_sand_solution.stix"
        )
        pts_old_pl1 = ds_solution.phreatic_line_points
        pts_old_pl2 = [
            (float(p.X), float(p.Z))
            for p in ds_solution.get_headline_by_label("Stijghoogtelijn 2 (PL2)").Points
        ]
        alg = AlgorithmPhreaticLine(
            ds=ds,
            river_level_mhw=18,
            river_level_ghw=11,
            polder_level=8,
            aquifer_label="L 3",
            hydraulic_head_pl2_inward=10,
            hydraulic_head_pl2_outward=10,
            intrusion_length=1,
            inward_leakage_length_pl3=750,
            outward_leakage_length_pl3=10,
        )
        ds = alg.execute()
        pts_new_pl1 = ds.phreatic_line_points
        # TODO > convert to points
        pts_new_pl2 = [
            (float(p.X), float(p.Z))
            for p in ds.get_headline_by_label("Stijghoogtelijn 2 (PL2)").Points
        ]
        plt.figure(figsize=(15, 5))
        plt.plot(
            [p[0] for p in pts_old_pl1],
            [p[1] for p in pts_old_pl1],
            "b--",
            label="PL1 solution",
        )
        plt.plot(
            [p[0] for p in pts_old_pl2],
            [p[1] for p in pts_old_pl2],
            "b",
            label="PL2 solution",
        )
        plt.plot(
            [p[0] for p in pts_new_pl1],
            [p[1] for p in pts_new_pl1],
            "r--",
            label="PL1 algorithm",
        )
        plt.plot(
            [p[0] for p in pts_new_pl2],
            [p[1] for p in pts_new_pl2],
            "r",
            label="PL2 algorithm",
        )
        plt.legend()
        plt.savefig("tests/testdata/output/test_pl_clay_on_sand.png")
        ds.serialize("tests/testdata/output/test_pl_clay_on_sand.stix")

    def test_sand_on_clay(self):
        ds = DStability.from_stix("tests/testdata/stix/pl_sand_on_clay.stix")
        ds_solution = DStability.from_stix(
            "tests/testdata/stix/solutions/pl_sand_on_clay_solution.stix"
        )
        pts_old_pl1 = ds_solution.phreatic_line_points
        alg = AlgorithmPhreaticLine(
            ds=ds,
            river_level_mhw=18,
            river_level_ghw=11,
            polder_level=8,
        )
        ds = alg.execute()
        pts_new_pl1 = ds.phreatic_line_points
        plt.figure(figsize=(15, 5))
        plt.plot(
            [p[0] for p in pts_old_pl1],
            [p[1] for p in pts_old_pl1],
            "b--",
            label="PL1 solution",
        )
        plt.plot(
            [p[0] for p in pts_new_pl1],
            [p[1] for p in pts_new_pl1],
            "k-",
            label="PL1 algorithm",
        )
        plt.legend()
        plt.savefig("tests/testdata/output/test_pl_sand_on_clay.png")
        ds.serialize("tests/testdata/output/test_pl_sand_on_clay.stix")

    def test_sand_on_sand(self):
        ds = DStability.from_stix("tests/testdata/stix/pl_sand_on_sand.stix")
        ds_solution = DStability.from_stix(
            "tests/testdata/stix/solutions/pl_sand_on_sand_solution.stix"
        )
        pts_old_pl1 = ds_solution.phreatic_line_points
        alg = AlgorithmPhreaticLine(
            ds=ds,
            river_level_mhw=18,
            river_level_ghw=11,
            polder_level=8,
        )
        ds = alg.execute()
        pts_new_pl1 = ds.phreatic_line_points
        plt.figure(figsize=(15, 5))
        plt.plot(
            [p[0] for p in pts_old_pl1],
            [p[1] for p in pts_old_pl1],
            "b--",
            label="PL1 solution",
        )
        plt.plot(
            [p[0] for p in pts_new_pl1],
            [p[1] for p in pts_new_pl1],
            "k-",
            label="PL1 algorithm",
        )
        plt.legend()
        plt.savefig("tests/testdata/output/test_pl_sand_on_sand.png")
        ds.serialize("tests/testdata/output/test_pl_sand_on_sand.stix")
