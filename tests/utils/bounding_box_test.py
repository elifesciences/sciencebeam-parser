from sciencebeam_parser.utils.bounding_box import BoundingBox


class TestBoundingBox:
    def test_should_calculate_area(self):
        bounding_box = BoundingBox(
            x=101, y=102, width=200, height=50
        )
        assert bounding_box.area == 200 * 50

    def test_should_scale_by_given_ratio(self):
        assert (
            BoundingBox(x=1, y=2, width=3, height=4).scale_by(10, 100)
            == BoundingBox(x=10, y=200, width=30, height=400)
        )

    def test_should_calculate_intersection_with_identical_bounding_box(self):
        bounding_box = BoundingBox(110, 120, 50, 60)
        assert (
            bounding_box.intersection(bounding_box) == bounding_box
        )

    def test_should_calculate_intersection_with_smaller_contained_bounding_box(self):
        assert (
            BoundingBox(100, 100, 200, 200).intersection(
                BoundingBox(110, 120, 50, 60)
            ) == BoundingBox(110, 120, 50, 60)
        )

    def test_should_calculate_intersection_with_larger_bounding_box(self):
        assert (
            BoundingBox(110, 120, 50, 60).intersection(
                BoundingBox(100, 100, 200, 200)
            ) == BoundingBox(110, 120, 50, 60)
        )

    def test_should_calculate_intersection_with_overlapping_bounding_box(self):
        assert (
            BoundingBox(110, 120, 50, 60).intersection(
                BoundingBox(120, 110, 100, 100)
            ) == BoundingBox(120, 120, 40, 60)
        )
