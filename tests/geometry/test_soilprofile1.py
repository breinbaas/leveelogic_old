from leveelogic.geometry.soilprofile1 import SoilProfile1
from leveelogic.soil.soilcollection import SoilCollection
from leveelogic.geometry.soillayer import SoilLayer


class TestSoilProfile1:
    def test_stresses(self):
        # waterlevel in top layer
        sp1 = SoilProfile1(
            soillayers=[
                SoilLayer(top=0.0, bottom=-2.0, soilcode="clay"),
                SoilLayer(top=-2.0, bottom=-5.0, soilcode="peat"),
                SoilLayer(top=-5.0, bottom=-10.0, soilcode="sand"),
            ],
            waterlevel=-1.0,
        )
        stresses = sp1.stresses(soilcollection=SoilCollection(), unit_weight_water=10.0)
        assert stresses[-1] == (-10, 65, 90, 155)

        # waterlevel above top layer
        sp1 = SoilProfile1(
            soillayers=[
                SoilLayer(top=0.0, bottom=-2.0, soilcode="clay"),
                SoilLayer(top=-2.0, bottom=-5.0, soilcode="peat"),
                SoilLayer(top=-5.0, bottom=-10.0, soilcode="sand"),
            ],
            waterlevel=1.0,
        )
        stresses = sp1.stresses(soilcollection=SoilCollection(), unit_weight_water=10.0)
        assert stresses[-1] == (-10, 55, 110, 165)

        # waterlevel in layer with different ysat / ydry
        sp1 = SoilProfile1(
            soillayers=[
                SoilLayer(top=0.0, bottom=-2.0, soilcode="clay"),
                SoilLayer(top=-2.0, bottom=-5.0, soilcode="peat"),
                SoilLayer(top=-5.0, bottom=-10.0, soilcode="sand"),
            ],
            waterlevel=-7.0,
        )
        stresses = sp1.stresses(soilcollection=SoilCollection(), unit_weight_water=10.0)
        assert stresses[-1] == (-10, 121, 30, 151)

        # no waterlevel (equals waterlevel below bottom of soilprofile)
        sp1 = SoilProfile1(
            soillayers=[
                SoilLayer(top=0.0, bottom=-2.0, soilcode="clay"),
                SoilLayer(top=-2.0, bottom=-5.0, soilcode="peat"),
                SoilLayer(top=-5.0, bottom=-10.0, soilcode="sand"),
            ],
        )
        stresses = sp1.stresses(soilcollection=SoilCollection(), unit_weight_water=10.0)
        assert stresses[-1] == (-10, 145, 0, 145)
