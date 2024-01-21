from leveelogic.geometry.soilprofile2 import SoilProfile2
from leveelogic.soilinvestigation.cpt import Cpt, CptConversionMethod


class TestDStability:
    def test_from_cpts(self):
        cpt_left = Cpt.from_file("tests/testdata/cpts/01.gef")
        cpt_right = Cpt.from_file("tests/testdata/cpts/02.gef")
        sp2 = SoilProfile2.from_cpts(
            surface=[
                (-10.0, 0.0),
                (0.0, 0.0),
                (5.0, 5.0),
                (10.0, 5.0),
                (20.0, -5.0),
                (40.0, -5.0),
            ],
            x_polder=8.0,
            cpt_left=cpt_left,
            cpt_right=cpt_right,
        )
        fig = sp2.plot()
        fig.savefig("tests/testdata/output/soilprofile2d.png")
