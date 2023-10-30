from leveelogic.deltares.algorithms.algorithm_mirror import AlgorithmMirror
from leveelogic.deltares.dstability import DStability
from leveelogic.geometry.characteristic_point import CharacteristicPointType


class TestAlgorithmMove:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        ds.set_characteristic_point(25, point_type=CharacteristicPointType.TOE_RIGHT)
        alg = AlgorithmMirror(ds=ds)
        ds = alg.execute()
        ds.serialize("tests/testdata/output/simple_geometry_mirrored.stix")
