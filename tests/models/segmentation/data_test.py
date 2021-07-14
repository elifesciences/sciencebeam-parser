import logging
from pygrobid.models.data import feature_linear_scaling_int

from pygrobid.document.layout_document import LayoutBlock, LayoutDocument, LayoutLine, LayoutPage

from pygrobid.models.segmentation.data import NBBINS_POSITION, SegmentationLineFeaturesProvider


LOGGER = logging.getLogger(__name__)


class TestSegmentationLineFeaturesProvider:
    def test_should_provide_page_and_block_status(self):
        layout_document = LayoutDocument(pages=[
            LayoutPage(blocks=[LayoutBlock(lines=[
                LayoutLine.for_text('line1'),
                LayoutLine.for_text('line2'),
                LayoutLine.for_text('line3')
            ])])
        ])
        features_provider = SegmentationLineFeaturesProvider()
        feature_values = []
        for features in features_provider.iter_line_features(layout_document):
            feature_values.append({
                'page_status': features.get_page_status(),
                'block_status': features.get_block_status()
            })
        LOGGER.debug('feature_values: %r', feature_values)
        assert feature_values == [
            {'page_status': 'PAGESTART', 'block_status': 'BLOCKSTART'},
            {'page_status': 'PAGEIN', 'block_status': 'BLOCKIN'},
            {'page_status': 'PAGEEND', 'block_status': 'BLOCKEND'}
        ]

    def test_should_provide_line_text(self):
        layout_document = LayoutDocument(pages=[
            LayoutPage(blocks=[LayoutBlock(lines=[
                LayoutLine.for_text('first1 second1 this is a line'),
                LayoutLine.for_text('first2 second2 this is a line')
            ])])
        ])
        features_provider = SegmentationLineFeaturesProvider()
        feature_values = []
        for features in features_provider.iter_line_features(layout_document):
            feature_values.append({
                'line_text': features.line_text,
                'token_text': features.token_text,
                'second_token_text': features.second_token_text
            })
        LOGGER.debug('feature_values: %r', feature_values)
        assert feature_values == [
            {
                'line_text': 'first1 second1 this is a line',
                'token_text': 'first1',
                'second_token_text': 'second1'
            },
            {
                'line_text': 'first2 second2 this is a line',
                'token_text': 'first2',
                'second_token_text': 'second2'
            },
        ]

    def test_should_provide_punctuation_profile(self):
        layout_document = LayoutDocument(pages=[
            LayoutPage(blocks=[LayoutBlock(lines=[
                LayoutLine.for_text('a .: b'),
            ])])
        ])
        features_provider = SegmentationLineFeaturesProvider()
        feature_values = []
        for features in features_provider.iter_line_features(layout_document):
            feature_values.append({
                'line_punctuation_profile': features.get_line_punctuation_profile(),
                'line_punctuation_profile_length_feature': (
                    features.get_line_punctuation_profile_length_feature()
                ),
            })
        LOGGER.debug('feature_values: %r', feature_values)
        assert feature_values == [
            {
                'line_punctuation_profile': '.:',
                'line_punctuation_profile_length_feature': '2'
            },
        ]

    def test_should_provide_block_relative_line_length(self):
        layout_document = LayoutDocument(pages=[
            LayoutPage(blocks=[LayoutBlock(lines=[
                LayoutLine.for_text('1'),
                LayoutLine.for_text('12'),
                LayoutLine.for_text('1234567890'),
            ])])
        ])
        features_provider = SegmentationLineFeaturesProvider()
        feature_values = []
        for features in features_provider.iter_line_features(layout_document):
            feature_values.append({
                'str_block_relative_line_length_feature': (
                    features.get_str_block_relative_line_length_feature()
                )
            })
        LOGGER.debug('feature_values: %r', feature_values)
        assert feature_values == [
            {
                'str_block_relative_line_length_feature': '1',  # 1 * 10 / 10
            },
            {
                'str_block_relative_line_length_feature': '2',  # 2 * 10 / 10
            },
            {
                'str_block_relative_line_length_feature': '10',  # 10 * 10 / 10
            },
        ]

    def test_should_provide_block_relative_document_token_position(self):
        layout_document = LayoutDocument(pages=[
            LayoutPage(blocks=[LayoutBlock(lines=[
                LayoutLine.for_text(f'line{i}')
                for i in range(10)
            ])])
        ])
        features_provider = SegmentationLineFeaturesProvider()
        feature_values = []
        for features in features_provider.iter_line_features(layout_document):
            feature_values.append({
                'str_relative_document_position': (
                    features.get_str_relative_document_position()
                )
            })
        LOGGER.debug('feature_values: %r', feature_values)
        assert feature_values == [
            {
                'str_relative_document_position': str(feature_linear_scaling_int(
                    i, 10, NBBINS_POSITION
                )),
            }
            for i in range(10)
        ]
