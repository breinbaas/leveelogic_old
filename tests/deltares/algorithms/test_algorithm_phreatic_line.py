from leveelogic.deltares.algorithms.algorithm_phreatic_line import AlgorithmPhreaticLine
from leveelogic.deltares.dstability import DStability
from leveelogic.geometry.characteristic_point import CharacteristicPointType


class TestAlgorithmPhreaticLine:
    def test_simple_no_pl(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry_no_pl.stix")
        ds.set_characteristic_point(
            10, point_type=CharacteristicPointType.REFERENCE_POINT
        )
        alg = AlgorithmPhreaticLine(
            ds=ds,
            waterlevel=4.0,
            waterlevel_polder=-11.0,
            waterlevel_offset=0.5,
            offset_points=[(1.0, 0.0), (2.0, -1.0)],
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/simple_geometry_with_pl.stix")

    def test_simple_with_pl(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        ds.set_characteristic_point(
            10, point_type=CharacteristicPointType.REFERENCE_POINT
        )
        alg = AlgorithmPhreaticLine(
            ds=ds,
            waterlevel=4.0,
            waterlevel_polder=-11.0,
            waterlevel_offset=0.5,
            offset_points=[(1.0, 0.0), (2.0, -1.0)],
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/simple_geometry_with_double_pl.stix")
