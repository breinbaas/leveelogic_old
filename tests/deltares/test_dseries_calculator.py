import pytest
import os
from pathlib import Path

from leveelogic.deltares.dseries_calculator import (
    DSeriesCalculator,
    CalculationModelType,
)
from leveelogic.deltares.dstability import DStability
from leveelogic.deltares.dgeoflow import DGeoFlow

# class TestDGeoFlow:
#     def test_parse(self):
#         dg = DGeoFlow.from_flox("tests/testdata/flox/simple.flox")
#         assert len(dg.soillayers) == 8


class TestDSeriesCalculator:
    def test_add_valid_models(self):
        """Testing if we can add models of the same type"""
        ds1 = DStability.from_stix("tests/testdata/stix/complex_geometry.stix")
        ds2 = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        dsc = DSeriesCalculator()
        dsc.add_model(ds1, "model 1")
        assert dsc.calculation_model_type == CalculationModelType.DSTABILITY
        dsc.add_model(ds2, "model 2")
        assert len(dsc.calculation_models) == 2

    def test_mixing_up_models_raises(self):
        """Testing if we cannot mix types of calculations"""
        ds1 = DStability.from_stix("tests/testdata/stix/complex_geometry.stix")
        dg1 = DGeoFlow.from_flox("tests/testdata/flox/simple.flox")
        dsc = DSeriesCalculator()
        dsc.add_model(ds1, "model 1")
        assert dsc.calculation_model_type == CalculationModelType.DSTABILITY
        with pytest.raises(ValueError):
            dsc.add_model(dg1, "model 2")

    def test_multithreaded(self):
        envfile = Path(os.getcwd()) / "leveelogic.env"
        if envfile.exists():
            ds1 = DStability.from_stix("tests/testdata/stix/complex_geometry.stix")
            ds2 = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
            dsc = DSeriesCalculator()
            dsc.add_models([ds1, ds2], ["model 1", "model 2"])
            assert len(dsc.calculation_models) == 2
            dsc.calculate()
            assert dsc.calculation_models[0].result.safety_factor == pytest.approx(
                1.382, abs=1e-3
            )
            assert dsc.calculation_models[1].result.safety_factor == pytest.approx(
                0.382, abs=1e-3
            )
