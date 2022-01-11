import logging
import os
import re
from pathlib import Path
from typing import Iterable, Iterator, Optional, Sequence
from unittest.mock import MagicMock, patch

import pytest

from lxml import etree


from sciencebeam_parser.utils.xml import get_text_content_list
from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutPage
)
from sciencebeam_parser.document.tei.common import get_tei_xpath_text_content_list
from sciencebeam_parser.models.data import DEFAULT_DOCUMENT_FEATURES_CONTEXT
from sciencebeam_parser.models.training_data import TeiTrainingDataGenerator
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
from sciencebeam_parser.models.name.training_data import (
    NameTeiTrainingDataGenerator
)
from sciencebeam_parser.models.figure.training_data import (
    FigureTeiTrainingDataGenerator
)
from sciencebeam_parser.models.table.training_data import (
    TableTeiTrainingDataGenerator
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

        self.author_surname_block = LayoutBlock.for_text('Author Surname 1')
        self.author_block = LayoutBlock.merge_blocks([self.author_surname_block])

        self.institution_block = LayoutBlock.for_text('Institution 1')
        self.affiliation_block = LayoutBlock.merge_blocks([self.institution_block])

        self.header_block = LayoutBlock.merge_blocks([
            self.title_block,
            self.author_block,
            self.affiliation_block
        ])

        self.figure_head_block = LayoutBlock.for_text('Figure 1')
        self.figure_block = LayoutBlock.merge_blocks([self.figure_head_block])

        self.table_head_block = LayoutBlock.for_text('Table 1')
        self.table_block = LayoutBlock.merge_blocks([self.table_head_block])

        self.body_section_title_block = LayoutBlock.for_text('Section 1')
        self.body_section_paragraph_block = LayoutBlock.for_text('Paragraph 1')
        self.body_block = LayoutBlock.merge_blocks([
            self.body_section_title_block,
            self.body_section_paragraph_block,
            self.figure_block,
            self.table_block
        ])

        self.ref_author_surname_block = LayoutBlock.for_text('Ref Author Surname 1')
        self.ref_author_block = LayoutBlock.merge_blocks([self.ref_author_surname_block])

        self.ref_label_block = LayoutBlock.for_text('1')
        self.ref_title_block = LayoutBlock.for_text('Reference 1')
        self.ref_text_block = LayoutBlock.merge_blocks([
            self.ref_title_block,
            self.ref_author_block
        ])
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
    name_header_model_mock = fulltext_models_mock.name_header_model_mock
    name_citation_model_mock = fulltext_models_mock.name_citation_model_mock
    affiliation_address_model_mock = fulltext_models_mock.affiliation_address_model_mock
    fulltext_model_mock = fulltext_models_mock.fulltext_model_mock
    reference_segmenter_model_mock = fulltext_models_mock.reference_segmenter_model_mock
    citation_model_mock = fulltext_models_mock.citation_model_mock
    figure_model_mock = fulltext_models_mock.figure_model_mock
    table_model_mock = fulltext_models_mock.table_model_mock

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
        doc.author_block, '<author>'
    )
    header_model_mock.update_label_by_layout_block(
        doc.affiliation_block, '<affiliation>'
    )

    affiliation_address_model_mock.update_label_by_layout_block(
        doc.institution_block, '<institution>'
    )

    name_header_model_mock.update_label_by_layout_block(
        doc.author_surname_block, '<surname>'
    )

    fulltext_model_mock.update_label_by_layout_block(
        doc.body_section_title_block, '<section>'
    )
    fulltext_model_mock.update_label_by_layout_block(
        doc.body_section_paragraph_block, '<paragraph>'
    )
    fulltext_model_mock.update_label_by_layout_block(
        doc.figure_block, '<figure>'
    )
    fulltext_model_mock.update_label_by_layout_block(
        doc.table_block, '<table>'
    )

    figure_model_mock.update_label_by_layout_block(
        doc.figure_head_block, '<figure_head>'
    )

    table_model_mock.update_label_by_layout_block(
        doc.table_head_block, '<figure_head>'
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
    citation_model_mock.update_label_by_layout_block(
        doc.ref_author_block, '<author>'
    )

    name_citation_model_mock.update_label_by_layout_block(
        doc.ref_author_surname_block, '<surname>'
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


def _get_expected_file_path_with_suffix(
    output_path: Path,
    source_filename: str,
    suffix: Optional[str],
    pre_file_path_suffix: str = ''
) -> Path:
    assert suffix
    source_name = os.path.splitext(os.path.basename(source_filename))[0]
    return output_path.joinpath(source_name + pre_file_path_suffix + suffix)


def _check_tei_training_data_generator_output_and_return_xml_root(
    tei_training_data_generator: TeiTrainingDataGenerator,
    output_path: Path,
    expect_raw_data: bool,
    source_filename: str = SOURCE_FILENAME_1,
    pre_file_path_suffix: str = ''
) -> etree.ElementBase:
    expected_segmentation_tei_path = _get_expected_file_path_with_suffix(
        output_path,
        source_filename,
        tei_training_data_generator.get_default_tei_filename_suffix(),
        pre_file_path_suffix=pre_file_path_suffix
    )
    assert expected_segmentation_tei_path.exists()
    if expect_raw_data:
        expected_segmentation_data_path = _get_expected_file_path_with_suffix(
            output_path,
            source_filename,
            tei_training_data_generator.get_default_data_filename_suffix(),
            pre_file_path_suffix=pre_file_path_suffix
        )
        assert expected_segmentation_data_path.exists()
    xml_root = etree.parse(str(expected_segmentation_tei_path)).getroot()
    LOGGER.debug('xml: %r', etree.tostring(xml_root))
    return xml_root


def _check_tei_training_data_generator_output(
    tei_training_data_generator: TeiTrainingDataGenerator,
    output_path: Path,
    expect_raw_data: bool,
    tei_xml_xpath: str,
    tei_expected_values: Sequence[str],
    **kwargs
):
    xml_root = _check_tei_training_data_generator_output_and_return_xml_root(
        tei_training_data_generator=tei_training_data_generator,
        output_path=output_path,
        expect_raw_data=expect_raw_data,
        **kwargs
    )
    assert normalize_whitespace_list(
        get_tei_xpath_text_content_list(xml_root, tei_xml_xpath)
    ) == [
        normalize_whitespace(tei_expected_value)
        for tei_expected_value in tei_expected_values
    ]


@log_on_exception
class TestGenerateTrainingDataForLayoutDocument:
    def test_should_generate_data_using_mock_models(  # noqa pylint: disable=too-many-locals, too-many-statements
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
            use_model=True,
            use_directory_structure=False
        )

        _check_tei_training_data_generator_output(
            SegmentationTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=True,
            tei_xml_xpath='text/front',
            tei_expected_values=[sample_layout_document.header_block.text]
        )

        _check_tei_training_data_generator_output(
            HeaderTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=True,
            tei_xml_xpath='text/front/docTitle/titlePart',
            tei_expected_values=[sample_layout_document.title_block.text]
        )

        _check_tei_training_data_generator_output(
            NameTeiTrainingDataGenerator(),
            pre_file_path_suffix='.header',
            output_path=output_path,
            expect_raw_data=False,
            tei_xml_xpath='//tei:author//tei:surname',
            tei_expected_values=[sample_layout_document.author_surname_block.text]
        )

        _check_tei_training_data_generator_output(
            NameTeiTrainingDataGenerator(),
            pre_file_path_suffix='.citations',
            output_path=output_path,
            expect_raw_data=False,
            tei_xml_xpath='//tei:author//tei:surname',
            tei_expected_values=[sample_layout_document.ref_author_surname_block.text]
        )

        _check_tei_training_data_generator_output(
            AffiliationAddressTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=False,
            tei_xml_xpath='//tei:affiliation/tei:orgName[@type="institution"]',
            tei_expected_values=[sample_layout_document.institution_block.text]
        )

        _check_tei_training_data_generator_output(
            FullTextTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=True,
            tei_xml_xpath='//head',
            tei_expected_values=[sample_layout_document.body_section_title_block.text]
        )

        _check_tei_training_data_generator_output(
            FigureTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=True,
            tei_xml_xpath='//head',
            tei_expected_values=[sample_layout_document.figure_head_block.text]
        )

        _check_tei_training_data_generator_output(
            TableTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=True,
            tei_xml_xpath='//head',
            tei_expected_values=[sample_layout_document.table_head_block.text]
        )

        _check_tei_training_data_generator_output(
            ReferenceSegmenterTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=True,
            tei_xml_xpath='//bibl',
            tei_expected_values=[sample_layout_document.ref_ref_block.text]
        )

        _check_tei_training_data_generator_output(
            CitationTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=False,
            tei_xml_xpath='//tei:bibl/tei:title[@level="a"]',
            tei_expected_values=[sample_layout_document.ref_title_block.text]
        )

    def test_not_should_generate_figure_data_if_not_present(  # noqa pylint: disable=too-many-locals, too-many-statements
        self,
        tmp_path: Path,
        sample_layout_document: SampleLayoutDocument,
        fulltext_models_mock: MockFullTextModels
    ):
        configure_fulltext_models_mock_with_sample_document(
            fulltext_models_mock,
            sample_layout_document
        )
        fulltext_models_mock.fulltext_model_mock.update_label_by_layout_block(
            sample_layout_document.figure_block, '<paragraph>'
        )

        output_path = tmp_path / 'output'
        output_path.mkdir()
        generate_training_data_for_layout_document(
            layout_document=sample_layout_document.layout_document,
            output_path=str(output_path),
            source_filename=SOURCE_FILENAME_1,
            document_features_context=DEFAULT_DOCUMENT_FEATURES_CONTEXT,
            fulltext_models=fulltext_models_mock,
            use_model=True,
            use_directory_structure=False
        )

        example_name = os.path.splitext(os.path.basename(SOURCE_FILENAME_1))[0]

        expected_figure_tei_path = output_path.joinpath(
            example_name + FigureTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        expected_figure_data_path = output_path.joinpath(
            example_name + FigureTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        assert not expected_figure_tei_path.exists()
        assert not expected_figure_data_path.exists()


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

        xml_root = _check_tei_training_data_generator_output_and_return_xml_root(
            SegmentationTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=True,
            source_filename=MINIMAL_EXAMPLE_PDF
        )
        assert get_text_content_list(xml_root.xpath('text'))
        assert not get_text_content_list(xml_root.xpath('text/front'))

        xml_root = _check_tei_training_data_generator_output_and_return_xml_root(
            HeaderTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=True,
            source_filename=MINIMAL_EXAMPLE_PDF
        )
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

        xml_root = _check_tei_training_data_generator_output_and_return_xml_root(
            SegmentationTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=True,
            source_filename=MINIMAL_EXAMPLE_PDF
        )
        assert get_text_content_list(xml_root.xpath('text/front'))

        xml_root = _check_tei_training_data_generator_output_and_return_xml_root(
            HeaderTeiTrainingDataGenerator(),
            output_path=output_path,
            expect_raw_data=True,
            source_filename=MINIMAL_EXAMPLE_PDF
        )
        assert get_text_content_list(xml_root.xpath('text/front'))

    def test_should_allow_to_use_directory_structure(
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
            '--use-directory-structure',
            f'--source-path={MINIMAL_EXAMPLE_PDF_PATTERN}',
            f'--output-path={output_path}'
        ])
        assert output_path.exists()

        expected_output_path_and_suffix_list = [(
            output_path / 'segmentation' / 'corpus' / 'tei',
            SegmentationTeiTrainingDataGenerator().get_default_tei_filename_suffix()
        ), (
            output_path / 'segmentation' / 'corpus' / 'raw',
            SegmentationTeiTrainingDataGenerator().get_default_data_filename_suffix()
        ), (
            output_path / 'header' / 'corpus' / 'tei',
            HeaderTeiTrainingDataGenerator().get_default_tei_filename_suffix()
        ), (
            output_path / 'header' / 'corpus' / 'raw',
            HeaderTeiTrainingDataGenerator().get_default_data_filename_suffix()
        ), (
            output_path / 'name' / 'header' / 'corpus',
            '.header' + NameTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        ), (
            output_path / 'name' / 'citation' / 'corpus',
            '.citations' + NameTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )]

        for model_output_path, suffix in expected_output_path_and_suffix_list:
            file_path = _get_expected_file_path_with_suffix(
                model_output_path,
                MINIMAL_EXAMPLE_PDF,
                suffix
            )
            assert file_path.exists()
