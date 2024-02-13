from leveelogic.deltares.algorithms.algorithm_phreatic_line import AlgorithmPhreaticLine
from leveelogic.deltares.dstability import DStability


class TestAlgorithmPhreaticLine:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry_no_pl.stix")
        alg = AlgorithmPhreaticLine(
            ds=ds,
            x_ref=10.0,
            waterlevel=4.0,
            waterlevel_polder=-11.0,
            waterlevel_offset=0.25,
        )
        ds = alg.execute()
        ds.serialize(f"tests/testdata/output/alg_phreatic_line_no_pl.stix")

    def test_execute_with_offset(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry_no_pl.stix")
        alg = AlgorithmPhreaticLine(
            ds=ds,
            x_ref=10.0,
            waterlevel=4.0,
            waterlevel_polder=-11.0,
            waterlevel_offset=0.25,
            offset_points=[(2.0, -1.0), (3.0, -1.5)],
        )
        ds = alg.execute()
        ds.serialize(f"tests/testdata/output/alg_phreatic_line_no_pl_with_offset.stix")

    def test_execute_replace_original_pl(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmPhreaticLine(
            ds=ds,
            x_ref=10.0,
            waterlevel=4.0,
            waterlevel_polder=-11.0,
            waterlevel_offset=0.25,
        )
        ds = alg.execute()
        ds.serialize(f"tests/testdata/output/alg_phreatic_line_replace_pl.stix")
