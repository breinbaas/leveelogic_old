from leveelogic.deltares.algorithms.algorithm_berm import AlgorithmBerm
from leveelogic.deltares.algorithms.algorithm import AlgorithmInputCheckError
from leveelogic.deltares.dstability import DStability
from leveelogic.geometry.characteristic_point import CharacteristicPointType
from pathlib import Path

import pytest


class TestAlgorithmBerm:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_alg_pl_wsbd.stix")
        alg = AlgorithmBerm(
            ds=ds,
            soilcode="Dijksmateriaal (klei)_K3_CPhi",
            slope_top=10,
            slope_bottom=1,
            height=2.0,
            width=6.0,
            characteristic_points=ds.characteristic_points,
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/fc_alg_pl_wsbd_berm.stix")

    def test_execute_only_fill_ditch(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_alg_pl_wsbd.stix")
        alg = AlgorithmBerm(
            ds=ds,
            slope_top=10,
            slope_bottom=1,
            fill_ditch=True,
            ditch_soilcode="K1",
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/fc_alg_pl_wsbd_fill_ditch.stix")

    def test_execute_fill_ditch(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_alg_pl_wsbd.stix")
        alg = AlgorithmBerm(
            ds=ds,
            soilcode="Dijksmateriaal (klei)_K3_CPhi",
            slope_top=10,
            slope_bottom=1,
            height=2.0,
            width=24.0,
            fill_ditch=True,
            ditch_soilcode="K1",
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/fc_alg_pl_wsbd_berm_fill_ditch.stix")

    def test_execute_spikey_geometry_no_ditch(self):
        ds = DStability.from_stix("tests/testdata/stix/spikey_geometry.stix")

        alg = AlgorithmBerm(
            ds=ds,
            soilcode="Embankment dry",
            slope_top=10,
            slope_bottom=2,
            height=5.0,
            width=10.0,
        )
        ds = alg.execute()
        ds.serialize(f"tests/testdata/output/spikey_geometry_berm.stix")

    def test_execute_invalid(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmBerm(
            ds=ds,
            soilcode="Invalid soiltype",
            slope_top=10,
            slope_bottom=1,
            height=2.0,
            width=6.0,
        )
        with pytest.raises(AlgorithmInputCheckError):
            ds = alg.execute()

    def test_execute_spikey_geometry_fixed_xz(self):
        ds = DStability.from_stix("tests/testdata/stix/spikey_geometry.stix")

        alg = AlgorithmBerm(
            ds=ds,
            soilcode="Embankment dry",
            slope_top=10,
            slope_bottom=2,
            fixed_x=45,
            fixed_z=14,
        )
        ds = alg.execute()
        ds.serialize(f"tests/testdata/output/spikey_geometry_berm_fixed_xz.stix")

    def test_multiple_scenarios(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmBerm(
            ds=ds,
            soilcode="Embankment dry",
            slope_top=10,
            slope_bottom=1,
            height=2.0,
            width=6.0,
        )
        ds = alg.execute()

        ds.set_scenario_and_stage(1, 0)
        alg.ds = ds  # update the model
        alg.width = 8.0
        alg.height = 2.0
        ds = alg.execute()
        ds.serialize(
            f"tests/testdata/output/simple_geometry_berm_multiple_scenarios.stix"
        )
