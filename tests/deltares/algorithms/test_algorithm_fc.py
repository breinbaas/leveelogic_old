from leveelogic.deltares.algorithms.algorithm_fc import AlgorithmFC
from leveelogic.deltares.dstability import DStability
from leveelogic.geometry.characteristic_point import CharacteristicPointType

import matplotlib.pyplot as plt


class TestAlgorithmFC:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_pl_sample.stix")
        alg = AlgorithmFC(ds=ds, min_level=2.0, max_level=4.5, step=0.5, dz=1.44)
        result = alg.execute()

        plt.plot(result["waterlevel"], result["reliability_index"], "o-")
        plt.xlabel("Water level [m]")
        plt.ylabel("Reliability index")
        plt.title("Fragility curve")
        plt.grid()
        plt.savefig("tests/testdata/output/fc_pl_sample.fragility_curve.png")
