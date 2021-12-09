import logging
import os
import re
from pathlib import Path
from typing import Iterable, Sequence

import pytest

from lxml import etree


from sciencebeam_parser.utils.xml import get_text_content_list
from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutPage
)
from sciencebeam_parser.document.tei.common import tei_xpath
from sciencebeam_parser.models.data import DEFAULT_DOCUMENT_FEATURES_CONTEXT
from sciencebeam_parser.models.segmentation.training_data import (
    SegmentationTeiTrainingDataGenerator
)
from sciencebeam_parser.models.header.training_data import HeaderTeiTrainingDataGenerator
from sciencebeam_parser.models.affiliation_address.training_data import (
    AffiliationAddressTeiTrainingDataGenerator
)
from sciencebeam_parser.training.cli.generate_data import (
    generate_training_data_for_layout_document,
    main
)

from tests.processors.fulltext.model_mocks import MockFullTextModels


LOGGER = logging.getLogger(__name__)

MINIMAL_EXAMPLE_PDF = 'test-data/minimal-example.pdf'
MINIMAL_EXAMPLE_PDF_PATTERN = 'test-data/minimal-example*.pdf'


SOURCE_FILENAME_1 = 'test1.pdf'


@pytest.fixture(name='fulltext_models_mock')
def _fulltext_models() -> MockFullTextModels:
    return MockFullTextModels()


def normalize_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def normalize_whitespace_list(text_iterable: Iterable[str]) -> Sequence[str]:
    return [
        normalize_whitespace(text)
        for text in text_iterable
    ]


class TestGenerateTrainingDataForLayoutDocument:
    def test_should_generate_data_using_mock_models(  # pylint: disable=too-many-locals
        self,
        tmp_path: Path,
        fulltext_models_mock: MockFullTextModels
    ):
        title_block = LayoutBlock.for_text('This is the title')
        institution_block = LayoutBlock.for_text('Institution 1')
        affiliation_block = LayoutBlock.merge_blocks([institution_block])
        header_block = LayoutBlock.merge_blocks([title_block, affiliation_block])
        body_block = LayoutBlock.for_text('This is the body')

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        header_model_mock = fulltext_models_mock.header_model_mock
        affiliation_address_model_mock = fulltext_models_mock.affiliation_address_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            header_block, '<header>'
        )
        segmentation_model_mock.update_label_by_layout_block(
            body_block, '<body>'
        )

        header_model_mock.update_label_by_layout_block(
            title_block, '<title>'
        )
        header_model_mock.update_label_by_layout_block(
            affiliation_block, '<affiliation>'
        )

        affiliation_address_model_mock.update_label_by_layout_block(
            institution_block, '<institution>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            header_block,
            body_block
        ])])

        output_path = tmp_path / 'output'
        output_path.mkdir()
        generate_training_data_for_layout_document(
            layout_document=layout_document,
            output_path=str(output_path),
            source_filename=SOURCE_FILENAME_1,
            document_features_context=DEFAULT_DOCUMENT_FEATURES_CONTEXT,
            fulltext_models=fulltext_models_mock,
            use_model=True
        )

        example_name = os.path.splitext(os.path.basename(SOURCE_FILENAME_1))[0]
        expected_segmentation_tei_path = output_path.joinpath(
            example_name + SegmentationTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        expected_segmentation_data_path = output_path.joinpath(
            example_name + SegmentationTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        assert expected_segmentation_tei_path.exists()
        assert expected_segmentation_data_path.exists()
        xml_root = etree.parse(str(expected_segmentation_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert normalize_whitespace_list(
            get_text_content_list(xml_root.xpath('text/front'))
        ) == [
            normalize_whitespace(header_block.text)
        ]

        expected_header_tei_path = output_path.joinpath(
            example_name + HeaderTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        expected_header_data_path = output_path.joinpath(
            example_name + HeaderTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        assert expected_header_tei_path.exists()
        assert expected_header_data_path.exists()
        xml_root = etree.parse(str(expected_header_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert normalize_whitespace_list(get_text_content_list(
            xml_root.xpath('text/front/docTitle/titlePart')
        )) == [
            normalize_whitespace(title_block.text)
        ]

        expected_aff_tei_path = output_path.joinpath(
            example_name + AffiliationAddressTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        assert expected_aff_tei_path.exists()
        xml_root = etree.parse(str(expected_aff_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert normalize_whitespace_list(get_text_content_list(
            tei_xpath(xml_root, '//tei:affiliation/tei:orgName[@type="institution"]')
        )) == [
            normalize_whitespace(institution_block.text)
        ]


# Note: tests are currently using actual model and are therefore slow
@pytest.mark.slow
class TestMain:
    def test_should_be_able_to_generate_segmentation_training_data(
        self,
        tmp_path: Path
    ):
        output_path = tmp_path / 'generated-data'
        main([
            f'--source-path={MINIMAL_EXAMPLE_PDF_PATTERN}',
            f'--output-path={output_path}'
        ])
        assert output_path.exists()
        example_name = os.path.splitext(os.path.basename(MINIMAL_EXAMPLE_PDF))[0]
        expected_segmentation_tei_path = output_path.joinpath(
            example_name + SegmentationTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        expected_segmentation_data_path = output_path.joinpath(
            example_name + SegmentationTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        assert expected_segmentation_tei_path.exists()
        assert expected_segmentation_data_path.exists()
        xml_root = etree.parse(str(expected_segmentation_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert get_text_content_list(xml_root.xpath('text'))
        assert not get_text_content_list(xml_root.xpath('text/front'))

        expected_header_tei_path = output_path.joinpath(
            example_name + HeaderTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        expected_header_data_path = output_path.joinpath(
            example_name + HeaderTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        assert expected_header_tei_path.exists()
        assert expected_header_data_path.exists()
        xml_root = etree.parse(str(expected_header_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert get_text_content_list(xml_root.xpath('text/front'))

    def test_should_be_able_to_generate_segmentation_training_data_using_model(
        self,
        tmp_path: Path
    ):
        output_path = tmp_path / 'generated-data'
        main([
            f'--source-path={MINIMAL_EXAMPLE_PDF_PATTERN}',
            f'--output-path={output_path}',
            '--use-model'
        ])
        assert output_path.exists()
        example_name = os.path.splitext(os.path.basename(MINIMAL_EXAMPLE_PDF))[0]
        expected_segmentation_tei_path = output_path.joinpath(
            example_name + SegmentationTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        expected_segmentation_data_path = output_path.joinpath(
            example_name + SegmentationTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        assert expected_segmentation_tei_path.exists()
        assert expected_segmentation_data_path.exists()
        xml_root = etree.parse(str(expected_segmentation_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert get_text_content_list(xml_root.xpath('text/front'))

        expected_header_tei_path = output_path.joinpath(
            example_name + HeaderTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        expected_header_data_path = output_path.joinpath(
            example_name + HeaderTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        assert expected_header_tei_path.exists()
        assert expected_header_data_path.exists()
        xml_root = etree.parse(str(expected_header_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert get_text_content_list(xml_root.xpath('text/front'))

        expected_aff_tei_path = output_path.joinpath(
            example_name + AffiliationAddressTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        assert expected_aff_tei_path.exists()
        xml_root = etree.parse(str(expected_aff_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
