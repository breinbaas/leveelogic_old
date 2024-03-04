from leveelogic.deltares.algorithms.algorithm_add_calculation_settings import (
    AlgorithmAddCalculationSettings,
)
from leveelogic.deltares.dstability import DStability


class TestAlgorithmAddCalculationSettings:
    def test_execute(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        alg = AlgorithmAddCalculationSettings(ds=ds)
        ds = alg.execute()
        ds.serialize(
            "tests/testdata/output/alg_add_calc_settings_simple_geometry_bbf.stix"
        )
