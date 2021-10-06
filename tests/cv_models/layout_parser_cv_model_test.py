import logging

from layoutparser.elements.layout_elements import Rectangle, TextBlock
from layoutparser.elements.layout import Layout

from sciencebeam_parser.utils.bounding_box import BoundingBox
from sciencebeam_parser.cv_models.layout_parser_cv_model import (
    LayoutParserComputerVisionModelResult
)


LOGGER = logging.getLogger(__name__)


class TestLayoutParserComputerVisionModelResult:
    def test_should_filter_by_score(self):
        layout = Layout([
            TextBlock(
                Rectangle(11, 10, 100, 100), text='block1', type='Test', score=0.4
            ),
            TextBlock(
                Rectangle(12, 10, 100, 100), text='block2', type='Test', score=0.5
            ),
            TextBlock(
                Rectangle(13, 10, 100, 100), text='block3', type='Test', score=0.6
            )
        ])
        result = LayoutParserComputerVisionModelResult(
            layout,
            score_threshold=0.5,
            avoid_overlapping=False
        )
        instances = result.get_instances_by_type_name('Test')
        LOGGER.debug('instances: %r', instances)
        bounding_boxes = [instance.get_bounding_box() for instance in instances]
        assert bounding_boxes == [
            BoundingBox(12, 10, 100 - 12, 100 - 10),
            BoundingBox(13, 10, 100 - 13, 100 - 10)
        ]

    def test_should_avoid_overlapping(self):
        layout = Layout([
            TextBlock(
                Rectangle(11, 10, 100, 100), text='block1', type='Test', score=0.6
            ),
            TextBlock(
                Rectangle(12, 10, 100, 100), text='block2', type='Test', score=0.5
            )
        ])
        result = LayoutParserComputerVisionModelResult(
            layout,
            score_threshold=0.0,
            avoid_overlapping=True
        )
        instances = result.get_instances_by_type_name('Test')
        LOGGER.debug('instances: %r', instances)
        bounding_boxes = [instance.get_bounding_box() for instance in instances]
        assert bounding_boxes == [
            BoundingBox(11, 10, 100 - 11, 100 - 10),
        ]

    def test_should_ignore_empty_bounding_boxes(self):
        layout = Layout([
            TextBlock(
                Rectangle(11, 10, 100, 10), text='block1', type='Test', score=0.6
            ),
            TextBlock(
                Rectangle(12, 10, 100, 100), text='block2', type='Test', score=0.5
            ),
            TextBlock(
                Rectangle(13, 10, 100, 10), text='block2', type='Test', score=0.4
            )
        ])
        result = LayoutParserComputerVisionModelResult(
            layout,
            score_threshold=0.0,
            avoid_overlapping=True
        )
        instances = result.get_instances_by_type_name('Test')
        LOGGER.debug('instances: %r', instances)
        bounding_boxes = [instance.get_bounding_box() for instance in instances]
        assert bounding_boxes == [
            BoundingBox(12, 10, 100 - 12, 100 - 10),
        ]
