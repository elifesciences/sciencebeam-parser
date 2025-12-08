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

    def test_should_equal_same_bounding_boxes(self):
        assert BoundingBox(11, 12, 101, 102) == BoundingBox(11, 12, 101, 102)

    def test_should_not_equal_bounding_boxes_with_different_x(self):
        assert BoundingBox(11, 12, 101, 102) != BoundingBox(99, 12, 101, 102)

    def test_should_not_equal_bounding_boxes_with_different_y(self):
        assert BoundingBox(11, 12, 101, 102) != BoundingBox(11, 99, 101, 102)

    def test_should_not_equal_bounding_boxes_with_different_width(self):
        assert BoundingBox(11, 12, 101, 102) != BoundingBox(11, 12, 999, 102)

    def test_should_not_equal_bounding_boxes_with_different_height(self):
        assert BoundingBox(11, 12, 101, 102) != BoundingBox(11, 12, 101, 999)

    def test_should_not_equal_none(self):
        assert not BoundingBox(  # pylint: disable=unnecessary-dunder-call
            11, 12, 101, 102
        ).__eq__(None)

    def test_should_indicate_empty_with_zero_width(self):
        bounding_box = BoundingBox(0, 0, 0, 100)
        assert bounding_box.is_empty()
        assert not bounding_box

    def test_should_indicate_empty_with_zero_height(self):
        bounding_box = BoundingBox(0, 0, 100, 0)
        assert bounding_box.is_empty()
        assert not bounding_box

    def test_should_indicate_not_be_empty_with_non_zero_width_and_height(self):
        bounding_box = BoundingBox(0, 0, 100, 100)
        assert not bounding_box.is_empty()
        assert bounding_box
