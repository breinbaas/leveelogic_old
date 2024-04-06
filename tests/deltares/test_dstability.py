import pytest

from leveelogic.deltares.dstability import DStability


class TestDStability:
    def test_parse(self):
        ds = DStability.from_stix("tests/testdata/stix/simple_geometry.stix")
        assert ds.remarks == "STBU"
        assert ds.scenario_label(0) == "Scenario 1"
        assert ds.scenario_label(1) == "Scenario 2"
        assert ds.stage_label(0, 0) == "Stage 1"
        assert ds.num_scenarios == 2
        assert ds.num_stages(0) == 1
        assert ds.num_stages(1) == 1

    def test_parse_complex(self):
        ds = DStability.from_stix("tests/testdata/stix/complex_geometry.stix")

    def test_from_soilprofileN(self, cpt_soilprofileN):
        crs_points = [
            (0, -2),
            (8, -2),
            (15, 5),
            (18, 5),
            (23, -2),
            (26, -2),
            (27, -3),
            (28, -3),
            (29, -2),
            (50, -2),
        ]
        ds = DStability.from_soilprofileN(
            cpt_soilprofileN,
            crosssection_points=crs_points,
            fill_material_bottom="sand",
            fill_material_top="clay",
        )
        ds.serialize("tests/testdata/output/from_soilprofileN.stix")

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

    def test_to_soilpolygons(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_pl_sample.stix")
        spgs = ds.soilpolygons
        assert len(spgs) == len(ds.model.datastructure.soillayers[0].SoilLayers)

    def test_soilprofile1_at(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_pl_sample.stix")
        sp1 = ds.soilprofile1_at(x=256)

    def test_set_scenario_and_stage_by_name(self):
        ds = DStability.from_stix("tests/testdata/stix/scenarios_and_stages.stix")
        with pytest.raises(ValueError):
            ds.set_scenario_and_stage_by_name("NotOnMyWatch", "OrMine")
        ds.set_scenario_and_stage_by_name("Norm", "Norm")
        assert ds.current_scenario_index == 1
        assert ds.current_stage_index == 1
        ds.set_scenario_and_stage_by_name("dagelijks", "dagelijks")
        assert ds.current_scenario_index == 0
        assert ds.current_stage_index == 0
        ds.set_scenario_and_stage_by_name("norm", "dagelijks")
        assert ds.current_scenario_index == 1
        assert ds.current_stage_index == 0

    def test_scenarios_and_stages(self):
        ds = DStability.from_stix("tests/testdata/stix/scenarios_and_stages.stix")
        ds.set_scenario_and_stage_by_name("Norm", "Norm")
        assert ds.phreatic_line.Points[0].Z == "3.04"
        ds.set_scenario_and_stage_by_name("Dagelijks", "dagelijks")
        assert ds.phreatic_line.Points[0].Z == "0.67"

    def test_add_stage_from_soilpolygons(self):
        ds = DStability.from_stix("tests/testdata/stix/scenarios_and_stages.stix")
        spgs = ds.stage_to_soilpolygons(scenario_index=0, stage_index=0)
        ds.add_stage_from_soilpolygons(soilpolygons=spgs)
        ds.serialize("tests/testdata/output/test_add_stage_from_soilpolygons.stix")

    def test_stage_to_soilpolygons(self):
        ds = DStability.from_stix("tests/testdata/stix/scenarios_and_stages.stix")
        spg = ds.stage_to_soilpolygons()
        assert len(spg) == 6

    def test_copy_waternet(self):
        ds = DStability.from_stix("tests/testdata/stix/fc_pl_sample.stix")
        old_stage_index = ds.current_stage_index
        spgs = ds.stage_to_soilpolygons()
        new_stage_index = ds.add_stage_from_soilpolygons(soilpolygons=spgs)
        ds.copy_waternet(
            ds.current_scenario_index,
            old_stage_index,
            ds.current_scenario_index,
            new_stage_index,
        )
        ds.serialize("tests/testdata/output/test_copy_waternet.stix")

    def test_add_stage(self):
        ds = DStability.from_stix("tests/testdata/stix/add_stage.stix")
        ds.add_stage()
        ds.serialize("tests/testdata/output/test_add_stage.stix")
