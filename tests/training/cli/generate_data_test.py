import logging
import os
import re
from pathlib import Path
from typing import Iterable, Iterator, Sequence
from unittest.mock import MagicMock, patch

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
from sciencebeam_parser.models.fulltext.training_data import FullTextTeiTrainingDataGenerator
from sciencebeam_parser.models.reference_segmenter.training_data import (
    ReferenceSegmenterTeiTrainingDataGenerator
)
from sciencebeam_parser.models.segmentation.training_data import (
    SegmentationTeiTrainingDataGenerator
)
from sciencebeam_parser.models.header.training_data import HeaderTeiTrainingDataGenerator
from sciencebeam_parser.models.affiliation_address.training_data import (
    AffiliationAddressTeiTrainingDataGenerator
)
from sciencebeam_parser.models.citation.training_data import (
    CitationTeiTrainingDataGenerator
)
import sciencebeam_parser.training.cli.generate_data as generate_data_module
from sciencebeam_parser.training.cli.generate_data import (
    generate_training_data_for_layout_document,
    main
)

from tests.processors.fulltext.model_mocks import MockFullTextModels
from tests.test_utils import log_on_exception


LOGGER = logging.getLogger(__name__)

MINIMAL_EXAMPLE_PDF = 'test-data/minimal-example.pdf'
MINIMAL_EXAMPLE_PDF_PATTERN = 'test-data/minimal-example*.pdf'


SOURCE_FILENAME_1 = 'test1.pdf'


class SampleLayoutDocument:
    def __init__(self) -> None:
        self.title_block = LayoutBlock.for_text('This is the title')
        self.institution_block = LayoutBlock.for_text('Institution 1')
        self.affiliation_block = LayoutBlock.merge_blocks([self.institution_block])
        self.header_block = LayoutBlock.merge_blocks([self.title_block, self.affiliation_block])
        self.body_section_title_block = LayoutBlock.for_text('Section 1')
        self.body_section_paragraph_block = LayoutBlock.for_text('Paragraph 1')
        self.body_block = LayoutBlock.merge_blocks([
            self.body_section_title_block,
            self.body_section_paragraph_block
        ])
        self.ref_label_block = LayoutBlock.for_text('1')
        self.ref_title_block = LayoutBlock.for_text('Reference 1')
        self.ref_text_block = LayoutBlock.merge_blocks([self.ref_title_block])
        self.ref_ref_block = LayoutBlock.merge_blocks([
            self.ref_label_block,
            self.ref_text_block
        ])

        self.layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            self.header_block,
            self.body_block,
            self.ref_ref_block
        ])])


def configure_fulltext_models_mock_with_sample_document(
    fulltext_models_mock: MockFullTextModels,
    sample_layout_document: SampleLayoutDocument
):
    doc = sample_layout_document
    segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
    header_model_mock = fulltext_models_mock.header_model_mock
    affiliation_address_model_mock = fulltext_models_mock.affiliation_address_model_mock
    fulltext_model_mock = fulltext_models_mock.fulltext_model_mock
    reference_segmenter_model_mock = fulltext_models_mock.reference_segmenter_model_mock
    citation_model_mock = fulltext_models_mock.citation_model_mock

    segmentation_model_mock.update_label_by_layout_block(
        doc.header_block, '<header>'
    )
    segmentation_model_mock.update_label_by_layout_block(
        doc.body_block, '<body>'
    )
    segmentation_model_mock.update_label_by_layout_block(
        doc.ref_ref_block, '<references>'
    )

    header_model_mock.update_label_by_layout_block(
        doc.title_block, '<title>'
    )
    header_model_mock.update_label_by_layout_block(
        doc.affiliation_block, '<affiliation>'
    )

    affiliation_address_model_mock.update_label_by_layout_block(
        doc.institution_block, '<institution>'
    )

    fulltext_model_mock.update_label_by_layout_block(
        doc.body_section_title_block, '<section>'
    )
    fulltext_model_mock.update_label_by_layout_block(
        doc.body_section_paragraph_block, '<paragraph>'
    )

    reference_segmenter_model_mock.update_label_by_layout_block(
        doc.ref_label_block, '<label>'
    )
    reference_segmenter_model_mock.update_label_by_layout_block(
        doc.ref_text_block, '<reference>'
    )

    citation_model_mock.update_label_by_layout_block(
        doc.ref_title_block, '<title>'
    )


@pytest.fixture(name='fulltext_models_mock')
def _fulltext_models_mock() -> MockFullTextModels:
    return MockFullTextModels()


@pytest.fixture(name='sciencebeam_parser_class_mock', autouse=True)
def _sciencebeam_parser_class_mock() -> Iterator[MockFullTextModels]:
    with patch.object(generate_data_module, 'ScienceBeamParser') as mock:
        yield mock


@pytest.fixture(name='sciencebeam_parser_mock', autouse=True)
def _sciencebeam_parser_mock(
    sciencebeam_parser_class_mock: MagicMock,
    fulltext_models_mock: MockFullTextModels
) -> MockFullTextModels:
    mock = MagicMock(name='ScienceBeamParser')
    mock.fulltext_models = fulltext_models_mock
    sciencebeam_parser_class_mock.from_config.return_value = mock
    return mock


@pytest.fixture(name='sample_layout_document')
def _sample_layout_document() -> SampleLayoutDocument:
    return SampleLayoutDocument()


@pytest.fixture(name='sciencebeam_parser_session_mock', autouse=True)
def _sciencebeam_parser_session_mock(
    sciencebeam_parser_mock: MagicMock
) -> MockFullTextModels:
    mock = MagicMock(name='ScienceBeamParserSession')
    sciencebeam_parser_mock.get_new_session.return_value.__enter__.return_value = mock
    return mock


@pytest.fixture(name='sciencebeam_parser_source_mock', autouse=True)
def _sciencebeam_parser_source_mock(
    sciencebeam_parser_session_mock: MagicMock,
    sample_layout_document: SampleLayoutDocument
) -> MockFullTextModels:
    mock = MagicMock(name='ScienceBeamParserSource')
    mock.get_layout_document.return_value = sample_layout_document.layout_document
    sciencebeam_parser_session_mock.get_source.return_value = mock
    return mock


def normalize_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def normalize_whitespace_list(text_iterable: Iterable[str]) -> Sequence[str]:
    return [
        normalize_whitespace(text)
        for text in text_iterable
    ]


@log_on_exception
class TestGenerateTrainingDataForLayoutDocument:
    def test_should_generate_data_using_mock_models(  # pylint: disable=too-many-locals
        self,
        tmp_path: Path,
        sample_layout_document: SampleLayoutDocument,
        fulltext_models_mock: MockFullTextModels
    ):
        configure_fulltext_models_mock_with_sample_document(
            fulltext_models_mock,
            sample_layout_document
        )

        output_path = tmp_path / 'output'
        output_path.mkdir()
        generate_training_data_for_layout_document(
            layout_document=sample_layout_document.layout_document,
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
            normalize_whitespace(sample_layout_document.header_block.text)
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
            normalize_whitespace(sample_layout_document.title_block.text)
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
            normalize_whitespace(sample_layout_document.institution_block.text)
        ]

        expected_fulltext_tei_path = output_path.joinpath(
            example_name + FullTextTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        expected_fulltext_data_path = output_path.joinpath(
            example_name + FullTextTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        assert expected_fulltext_tei_path.exists()
        assert expected_fulltext_data_path.exists()
        xml_root = etree.parse(str(expected_fulltext_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert normalize_whitespace_list(get_text_content_list(
            tei_xpath(xml_root, '//head')
        )) == [
            normalize_whitespace(sample_layout_document.body_section_title_block.text)
        ]

        expected_ref_seg_tei_path = output_path.joinpath(
            example_name + ReferenceSegmenterTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        expected_ref_seg_data_path = output_path.joinpath(
            example_name + ReferenceSegmenterTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        assert expected_ref_seg_tei_path.exists()
        assert expected_ref_seg_data_path.exists()
        xml_root = etree.parse(str(expected_ref_seg_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert normalize_whitespace_list(get_text_content_list(
            tei_xpath(xml_root, '//bibl')
        )) == [
            normalize_whitespace(sample_layout_document.ref_ref_block.text)
        ]

        expected_citation_tei_path = output_path.joinpath(
            example_name + CitationTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        assert expected_citation_tei_path.exists()
        xml_root = etree.parse(str(expected_citation_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert normalize_whitespace_list(get_text_content_list(
            tei_xpath(xml_root, '//tei:bibl/tei:title[@level="a"]')
        )) == [
            normalize_whitespace(sample_layout_document.ref_title_block.text)
        ]
        assert normalize_whitespace_list(get_text_content_list(
            tei_xpath(xml_root, '//tei:bibl')
        )) == [
            normalize_whitespace(sample_layout_document.ref_title_block.text)
        ]


@log_on_exception
class TestMain:
    def test_should_be_able_to_generate_segmentation_training_data(
        self,
        tmp_path: Path,
        sample_layout_document: SampleLayoutDocument,
        fulltext_models_mock: MockFullTextModels
    ):
        configure_fulltext_models_mock_with_sample_document(
            fulltext_models_mock,
            sample_layout_document
        )
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
        tmp_path: Path,
        sample_layout_document: SampleLayoutDocument,
        fulltext_models_mock: MockFullTextModels
    ):
        configure_fulltext_models_mock_with_sample_document(
            fulltext_models_mock,
            sample_layout_document
        )
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
