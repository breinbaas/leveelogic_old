import pytest

from leveelogic.deltares.dgeoflow import DGeoFlow


class TestDGeoFlow:
    def test_parse(self):
        dg = DGeoFlow.from_flox("tests/testdata/flox/simple.flox")
        assert len(dg.soillayers) == 8
