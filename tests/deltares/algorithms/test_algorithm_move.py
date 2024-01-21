from leveelogic.deltares.algorithms.algorithm_move import AlgorithmMove
from leveelogic.deltares.dstability import DStability
from leveelogic.geometry.characteristic_point import CharacteristicPointType


class TestAlgorithmMove:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        xs = [p[0] for p in ds.points]
        dx = 10.0
        alg = AlgorithmMove(ds=ds, dx=dx)
        ds = alg.execute()
        xs_moved = [p[0] for p in ds.points]
        assert xs_moved == [p + dx for p in xs]
        ds.serialize("tests/testdata/output/moved.stix")
