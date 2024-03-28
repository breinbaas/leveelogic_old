from leveelogic.deltares.algorithms.algorithm_add_calculation_settings import (
    AlgorithmAddCalculationSettings,
)
from leveelogic.deltares.dstability import DStability


class TestAlgorithmAddCalculationSettings:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")

        # add calculation settings to scenario 0, stage 0
        alg = AlgorithmAddCalculationSettings(ds=ds)
        ds = alg.execute()

        # add calculation settings to scenario 1, stage 0
        ds.set_scenario_and_stage(1, 0)
        alg = AlgorithmAddCalculationSettings(ds=ds, bbf_space=0.5)
        ds = alg.execute()

        ds.serialize(
            "tests/testdata/output/alg_add_calc_settings_simple_geometry_bbf.stix"
        )
