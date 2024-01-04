from leveelogic.api.bro_api import BROAPI


class TestBROAPI:
    def test__get_cpt_metadata_by_bounds(self):
        api = BROAPI()
        cpt_characteristics = api._get_cpt_metadata_by_bounds(
            left=52.128694, bottom=4.608265, right=52.13233, top=4.622127
        )
        assert len(cpt_characteristics) > 0

    def test__get_cpt_metadata_by_bounds_limited(self):
        api = BROAPI()
        cpt_characteristics = api._get_cpt_metadata_by_bounds(
            left=52.128694, bottom=4.608265, right=52.13233, top=4.622127, max_num=3
        )
        assert len(cpt_characteristics) == 3

    def test_get_cpts_by_bounds(self):
        api = BROAPI()
        cpts = api.get_cpts_by_bounds(
            left=52.128694, bottom=4.608265, right=52.13233, top=4.622127, max_num=1
        )
        assert len(cpts) == 1
