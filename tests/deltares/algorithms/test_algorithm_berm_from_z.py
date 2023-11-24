from leveelogic.deltares.algorithms.algorithm_berm_from_z import AlgorithmBermFromZ
from leveelogic.deltares.dstability import DStability
from leveelogic.geometry.characteristic_point import CharacteristicPointType


class TestAlgorithmBermFromZ:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmBermFromZ(
            ds=ds,
            soilcode="H_Rk_ko",
            required_sf=0.7,
            x_base=25.0,
            angle=20,
            initial_height=1.0,
            slope_top=10,
            slope_side=1,
            step_size=1.0,
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/simple_geometry_berm_from_z.stix")

    def test_execute_2(self):
        ds = DStability.from_stix("tests/testdata/stix/real_sample_2.stix")
        alg = AlgorithmBermFromZ(
            ds=ds,
            soilcode="H_Rk_ko",
            required_sf=1.0,
            x_base=102.0,
            angle=20,
            initial_height=1.0,
            slope_top=10,
            slope_side=1,
            step_size=0.25,
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/simple_geometry_berm_from_z.stix")

    def test_execute_spikey_geometry(self):
        ds = DStability.from_stix("tests/testdata/stix/spikey_geometry.stix")
        alg = AlgorithmBermFromZ(
            ds=ds,
            soilcode="H_Rk_ko",
            required_sf=0.8,
            x_base=37,
            angle=20,
            initial_height=4.0,
            slope_top=10,
            slope_side=2,
            step_size=1.0,
            save_files=True,
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/simple_geometry_berm_from_z.stix")

    def test_execute_fc_pl_sample(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_pl_sample.stix")
        alg = AlgorithmBermFromZ(
            ds=ds,
            soilcode="Dijksmateriaal (klei)_K3_Su",
            required_sf=1.0,
            x_base=268,
            angle=20,
            initial_height=1.0,
            slope_top=10,
            slope_side=2,
            step_size=0.2,
            save_files=True,
        )
        ds = alg.execute()
        ds.serialize("tests/testdata/output/fc_pl_sample_berm_from_z.stix")
