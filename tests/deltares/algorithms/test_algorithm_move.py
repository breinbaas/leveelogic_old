from leveelogic.deltares.algorithms.algorithm_move import AlgorithmMove
from leveelogic.deltares.dstability import DStability
from leveelogic.geometry.characteristic_point import CharacteristicPointType


class TestAlgorithmMove:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        ds.set_characteristic_point(25, point_type=CharacteristicPointType.TOE_RIGHT)
        xs = [p[0] for p in ds.points]
        dx = 10.0
        alg = AlgorithmMove(ds=ds, dx=dx)
        ds = alg.execute()
        xs_moved = [p[0] for p in ds.points]
        assert xs_moved == [p + dx for p in xs]
        assert (
            ds.get_characteristic_point(point_type=CharacteristicPointType.TOE_RIGHT).x
            == 35
        )
