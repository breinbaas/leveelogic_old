import pytest

from leveelogic.deltares.dgeoflow import DGeoFlow


class TestDGeoFlow:
    def test_parse(self):
        dg = DGeoFlow.from_flox("tests/testdata/flox/simple.flox")
        # assert ds.remarks == "STBU"
        # assert ds.scenario_label(0) == "Alle STBI berekeningen"
        # assert ds.stage_label(0, 0) == "STBI fase 1"
        # assert ds.num_scenarios == 1
        # assert ds.num_stages(0) == 1
