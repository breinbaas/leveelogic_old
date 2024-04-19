from leveelogic.helpers import *


class TestHelpers:

    def test_get_top_of_polygon(self):
        polygon_points = [(0, 0), (10, 0), (10, -10), (0, -10)]
        assert get_top_of_polygon(polygon_points) == [(0, 0), (10, 0)]
        polygon_points = [(10, 0), (10, -10), (0, -10), (0, 0)]
        assert get_top_of_polygon(polygon_points) == [(0, 0), (10, 0)]
        polygon_points = [(10, -10), (0, -10), (0, 0), (10, 0)]
        assert get_top_of_polygon(polygon_points) == [(0, 0), (10, 0)]
        polygon_points = [(0, -10), (0, 0), (10, 0), (10, -10)]
        assert get_top_of_polygon(polygon_points) == [(0, 0), (10, 0)]

    def test_get_bottom_of_polygon(self):
        polygon_points = [(0, 0), (10, 0), (10, -10), (0, -10)]
        assert get_bottom_of_polygon(polygon_points) == [(0, -10), (10, -10)]
        polygon_points = [(10, 0), (10, -10), (0, -10), (0, 0)]
        assert get_bottom_of_polygon(polygon_points) == [(0, -10), (10, -10)]
        polygon_points = [(10, -10), (0, -10), (0, 0), (10, 0)]
        assert get_bottom_of_polygon(polygon_points) == [(0, -10), (10, -10)]
        polygon_points = [(0, -10), (0, 0), (10, 0), (10, -10)]
        assert get_bottom_of_polygon(polygon_points) == [(0, -10), (10, -10)]
