from leveelogic.geometry.soilprofileN import SoilProfileN
from leveelogic.soilinvestigation.cpt import Cpt, CptConversionMethod
from leveelogic.helpers import plot_soilpolygons
from leveelogic.soil.soilcollection import SoilCollection


class TestSoilProfileN:
    def test_from_cpts(self):
        cpt_left = Cpt.from_file("tests/testdata/cpts/01.gef")
        cpt_right = Cpt.from_file("tests/testdata/cpts/02.gef")

        spN = SoilProfileN()
        spN.append(
            cpt_left.to_soilprofile1(
                cptconversionmethod=CptConversionMethod.ROBERTSON,
                minimum_layerheight=0.5,
                peat_friction_ratio=6.0,
                left=0,
                right=20,
            )
        )
        spN.append(
            cpt_right.to_soilprofile1(
                cptconversionmethod=CptConversionMethod.ROBERTSON,
                minimum_layerheight=0.5,
                peat_friction_ratio=6.0,
                left=20,
                right=50,
            ),
            fill_material_bottom="bottom_material",
            fill_material_top="top_material",
        )
        assert spN.top == spN.soilprofiles[0].top
        assert spN.bottom == spN.soilprofiles[0].bottom
        fig = spN.plot()
        fig.savefig("tests/testdata/output/soilprofileN.png")

    def test_to_soilpolygons(self, cpt_soilprofileN):
        soilcollection = SoilCollection()
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
        spgs = cpt_soilprofileN.to_soilpolygons(
            crosssection_points=crs_points,
            fill_material_top="clay",
            fill_material_bottom="sand",
        )
        fig = plot_soilpolygons(spgs, soilcollection=soilcollection)
        fig.savefig("tests/testdata/output/soilprofileN_soilpolygons.png")
