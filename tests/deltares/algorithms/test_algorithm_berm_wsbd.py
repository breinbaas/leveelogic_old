from leveelogic.deltares.algorithms.algorithm_berm_wsbd import AlgorithmBermWSBD
from leveelogic.deltares.algorithms.algorithm import AlgorithmInputCheckError
from leveelogic.deltares.dstability import DStability
from leveelogic.geometry.characteristic_point import CharacteristicPointType
from pathlib import Path

import pytest


class TestAlgorithmBermWSBD:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_alg_pl_wsbd.stix")
        alg = AlgorithmBermWSBD(
            ds=ds,
            soilcode="Dijksmateriaal (klei)_K3_CPhi",
            slope_top=10,
            slope_bottom=1,
            initial_height=2.0,
            initial_width=6.0,
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/fc_alg_pl_wsbd_berm.stix")

    def test_execute_invalid(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmBermWSBD(
            ds=ds,
            soilcode="Embankment dry",
            slope_top=10,
            slope_bottom=1,
            initial_height=2.0,
            initial_width=6.0,
        )
        with pytest.raises(AlgorithmInputCheckError):
            ds = alg.execute()
