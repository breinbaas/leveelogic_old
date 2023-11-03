from leveelogic.deltares.dstability import DStability


class TestDStability:
    def test_parse(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        assert ds.remarks == "STBU"
        assert ds.scenario_label(0) == "Alle STBI berekeningen"
        assert ds.stage_label(0, 0) == "STBI fase 1"
        assert ds.num_scenarios == 1
        assert ds.num_stages(0) == 1

    def test_parse_complex(self):
        ds = DStability.from_stix("tests/testdata/stix/complex_geometry.stix")
