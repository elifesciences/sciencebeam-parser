import PIL.Image

from sciencebeam_parser.utils.image import get_image_with_max_resolution


class TestGetImageWithMaxResolution:
    def test_should_return_passed_in_image_if_below_threshold(self):
        image = PIL.Image.new('RGB', (10, 20))
        assert get_image_with_max_resolution(image, 20) == image

    def test_should_resize_based_on_width(self):
        image = PIL.Image.new('RGB', (40, 20))
        assert get_image_with_max_resolution(image, 20).size == (20, 10)

    def test_should_resize_based_on_height(self):
        image = PIL.Image.new('RGB', (20, 40))
        assert get_image_with_max_resolution(image, 20).size == (10, 20)
