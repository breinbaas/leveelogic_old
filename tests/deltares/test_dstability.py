import pytest

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

    def test_extract_soilparameters(self):
        ds = DStability.from_stix("tests/testdata/stix/complex_geometry.stix")
        lines = ds.extract_soilparameters()
        assert len(lines) == 26

    def test_safety_factor_to_dict(self):
        ds = DStability.from_stix("tests/testdata/stix/complex_geometry.stix")
        d = ds.safety_factor_to_dict(1, 0)
        i = 1

    def test_surface_intersections(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        intersections = ds.surface_intersections([(ds.left, 3.0), (ds.right, 3.0)])
        assert len(intersections) == 2
        assert intersections[0] == (8.0, 3.0)

    def test_get_headlines_coordinates(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_pl_sample.stix")
        hl_points = ds.get_headline_coordinates("Stijghoogtelijn 3 (PL3)")
        assert len(hl_points) == 26
