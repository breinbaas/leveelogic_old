from leveelogic.deltares.dstability import DStability


class TestDStability:
    def test_parse(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        assert ds.remarks == "STBU"
        assert ds.scenario_name(0) == "Alle STBI berekeningen"
        assert ds.stage_name(0, 0) == "STBI fase 1"
        assert ds.num_scenarios == 1
        assert ds.num_stages(0) == 1
