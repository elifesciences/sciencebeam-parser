# pylint: disable=not-callable
import logging
from pathlib import Path
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest

from lxml import etree
from lxml.builder import E

from sciencebeam_trainer_delft.sequence_labelling.reader import (
    load_data_crf_lines,
    load_data_and_labels_crf_file
)
from sciencebeam_parser.document.layout_document import LayoutBlock, LayoutDocument

from sciencebeam_parser.document.tei.common import TEI_E
from sciencebeam_parser.models.data import DocumentFeaturesContext

import sciencebeam_parser.training.cli.generate_delft_data as generate_delft_data_module
from sciencebeam_parser.training.cli.generate_delft_data import (
    main
)
from sciencebeam_parser.utils.xml_writer import XmlTreeWriter
from tests.processors.fulltext.model_mocks import MockFullTextModels

from tests.test_utils import log_on_exception


LOGGER = logging.getLogger(__name__)

MINIMAL_EXAMPLE_PDF = 'test-data/minimal-example.pdf'
MINIMAL_EXAMPLE_PDF_PATTERN = 'test-data/minimal-example*.pdf'


SOURCE_FILENAME_1 = 'test1.pdf'


TOKEN_1 = 'token1'
TOKEN_2 = 'token2'
TOKEN_3 = 'token3'


@pytest.fixture(autouse=True)
def _patch_sciencebeam_parser_class_mock(
    sciencebeam_parser_class_mock: MagicMock
) -> Iterator[MagicMock]:
    with patch.object(
        generate_delft_data_module, 'ScienceBeamParser', sciencebeam_parser_class_mock
    ) as mock:
        yield mock


@pytest.fixture(name='document_features_context')
def _document_features_context(
    sciencebeam_parser_mock: MagicMock
) -> DocumentFeaturesContext:
    return DocumentFeaturesContext(
        sciencebeam_parser_mock.app_features_context
    )


@log_on_exception
class TestMain:
    def test_should_be_able_to_generate_segmentation_training_data(
        self,
        tmp_path: Path
    ):
        tei_source_path = tmp_path / 'tei'
        raw_source_path = tmp_path / 'raw'
        output_path = tmp_path / 'output.data'
        tei_source_path.mkdir(parents=True, exist_ok=True)
        (tei_source_path / 'sample.segmentation.tei.xml').write_bytes(etree.tostring(
            E('tei', E('text', *[
                E('front', TOKEN_1, E('lb')),
                '\n',
                E('body', TOKEN_2, E('lb')),
                '\n'
            ]))
        ))
        raw_source_path.mkdir(parents=True, exist_ok=True)
        (raw_source_path / 'sample.segmentation').write_text('\n'.join([
            '{TOKEN_1} 1.1 1.2 1.3',
            '{TOKEN_2} 2.1 2.2 2.3'
        ]))
        main([
            '--model-name=segmentation',
            f'--tei-source-path={tei_source_path}/*.tei.xml',
            f'--raw-source-path={raw_source_path}',
            f'--delft-output-path={output_path}'
        ])
        assert output_path.exists()
        texts, _labels, _features = load_data_and_labels_crf_file(
            str(output_path)
        )
        LOGGER.debug('texts: %r', texts)
        assert len(texts) == 1
        assert list(texts[0]) == [TOKEN_1, TOKEN_2]
        assert list(_labels[0]) == ['B-<header>', 'B-<body>']
        assert _features.tolist() == [[
            ['1.1', '1.2', '1.3'],
            ['2.1', '2.2', '2.3']
        ]]

    def test_should_be_able_to_generate_header_training_data(
        self,
        tmp_path: Path
    ):
        tei_source_path = tmp_path / 'tei'
        raw_source_path = tmp_path / 'raw'
        output_path = tmp_path / 'output.data'
        tei_source_path.mkdir(parents=True, exist_ok=True)
        (tei_source_path / 'sample.segmentation.tei.xml').write_bytes(etree.tostring(
            E('tei', E('text', E('front', *[
                E('docTitle', E('titlePart', TOKEN_1, E('lb'))),
                '\n',
                E('byline', E('docAuthor', TOKEN_2, E('lb'))),
                '\n'
            ])))
        ))
        raw_source_path.mkdir(parents=True, exist_ok=True)
        (raw_source_path / 'sample.segmentation').write_text('\n'.join([
            '{TOKEN_1} 1.1 1.2 1.3',
            '{TOKEN_2} 2.1 2.2 2.3'
        ]))
        main([
            '--model-name=header',
            f'--tei-source-path={tei_source_path}/*.tei.xml',
            f'--raw-source-path={raw_source_path}',
            f'--delft-output-path={output_path}'
        ])
        assert output_path.exists()
        texts, _labels, _features = load_data_and_labels_crf_file(
            str(output_path)
        )
        LOGGER.debug('texts: %r', texts)
        assert len(texts) == 1
        assert list(texts[0]) == [TOKEN_1, TOKEN_2]
        assert list(_labels[0]) == ['B-<title>', 'B-<author>']
        assert _features.tolist() == [[
            ['1.1', '1.2', '1.3'],
            ['2.1', '2.2', '2.3']
        ]]

    def test_should_be_able_to_generate_figure_training_data(
        self,
        tmp_path: Path
    ):
        tei_source_path = tmp_path / 'tei'
        raw_source_path = tmp_path / 'raw'
        output_path = tmp_path / 'output.data'
        tei_source_path.mkdir(parents=True, exist_ok=True)
        (tei_source_path / 'sample.figure.tei.xml').write_bytes(etree.tostring(
            E('tei', E('text', *[
                E('figure', E('figDesc', TOKEN_1, E('lb'), '\n', TOKEN_2, E('lb'))),
                '\n'
            ]))
        ))
        raw_source_path.mkdir(parents=True, exist_ok=True)
        (raw_source_path / 'sample.figure').write_text('\n'.join([
            '{TOKEN_1} 1.1 1.2 1.3',
            '{TOKEN_2} 2.1 2.2 2.3'
        ]))
        main([
            '--model-name=figure',
            f'--tei-source-path={tei_source_path}/*.tei.xml',
            f'--raw-source-path={raw_source_path}',
            f'--delft-output-path={output_path}'
        ])
        assert output_path.exists()
        texts, _labels, _features = load_data_and_labels_crf_file(
            str(output_path)
        )
        LOGGER.debug('texts: %r', texts)
        assert len(texts) == 1
        assert list(texts[0]) == [TOKEN_1, TOKEN_2]
        assert list(_labels[0]) == ['B-<figDesc>', 'I-<figDesc>']
        assert _features.tolist() == [[
            ['1.1', '1.2', '1.3'],
            ['2.1', '2.2', '2.3']
        ]]

    def test_should_be_able_to_generate_affiliation_address_training_data(
        self,
        tmp_path: Path,
        fulltext_models_mock: MockFullTextModels,
        document_features_context: DocumentFeaturesContext
    ):
        data_generator = fulltext_models_mock.affiliation_address_model.get_data_generator(
            document_features_context=document_features_context
        )
        tei_source_path = tmp_path / 'tei'
        output_path = tmp_path / 'output.data'
        tei_source_path.mkdir(parents=True, exist_ok=True)
        xml_writer = XmlTreeWriter(TEI_E('tei'), element_maker=TEI_E)
        xml_writer.require_path([
            'teiHeader', 'fileDesc', 'sourceDesc', 'biblStruct', 'analytic', 'author',
            'affiliation', 'orgName[@type="institution"]'
        ])
        xml_writer.append_text(' '.join([TOKEN_1, TOKEN_2]))
        (tei_source_path / 'sample.affiliation.tei.xml').write_bytes(etree.tostring(
            xml_writer.root
        ))
        main([
            '--model-name=affiliation_address',
            f'--tei-source-path={tei_source_path}/*.tei.xml',
            f'--delft-output-path={output_path}'
        ])
        assert output_path.exists()
        layout_document = LayoutDocument.for_blocks([
            LayoutBlock.for_text(' '.join([TOKEN_1, TOKEN_2]))
        ])
        expected_data_lines = list(data_generator.iter_data_lines_for_layout_document(
            layout_document
        ))
        _expected_texts, expected_features = load_data_crf_lines(expected_data_lines)
        LOGGER.debug('expected_features: %r', expected_features)
        texts, labels, features = load_data_and_labels_crf_file(
            str(output_path)
        )
        LOGGER.debug('texts: %r', texts)
        LOGGER.debug('labels: %r', labels)
        LOGGER.debug('features: %r', features)
        LOGGER.debug('training tei: %r', etree.tostring(xml_writer.root))
        assert len(texts) == 1
        assert list(texts[0]) == [TOKEN_1, TOKEN_2]
        assert list(labels[0]) == ['B-<institution>', 'I-<institution>']
        assert features.tolist() == expected_features.tolist()

    def test_should_be_able_to_generate_citation_training_data(
        self,
        tmp_path: Path,
        fulltext_models_mock: MockFullTextModels,
        document_features_context: DocumentFeaturesContext
    ):
        data_generator = fulltext_models_mock.citation_model.get_data_generator(
            document_features_context=document_features_context
        )
        tei_source_path = tmp_path / 'tei'
        output_path = tmp_path / 'output.data'
        tei_source_path.mkdir(parents=True, exist_ok=True)
        xml_writer = XmlTreeWriter(TEI_E('tei'), element_maker=TEI_E)
        xml_writer.require_path(['text', 'back', 'listBibl', 'bibl', 'author'])
        xml_writer.append_text(' '.join([TOKEN_1, TOKEN_2]))
        (tei_source_path / 'sample.references.tei.xml').write_bytes(etree.tostring(
            xml_writer.root
        ))
        main([
            '--model-name=citation',
            f'--tei-source-path={tei_source_path}/*.tei.xml',
            f'--delft-output-path={output_path}'
        ])
        assert output_path.exists()
        layout_document = LayoutDocument.for_blocks([
            LayoutBlock.for_text(' '.join([TOKEN_1, TOKEN_2]))
        ])
        expected_data_lines = list(data_generator.iter_data_lines_for_layout_document(
            layout_document
        ))
        _expected_texts, expected_features = load_data_crf_lines(expected_data_lines)
        LOGGER.debug('expected_features: %r', expected_features)
        texts, labels, features = load_data_and_labels_crf_file(
            str(output_path)
        )
        LOGGER.debug('texts: %r', texts)
        LOGGER.debug('labels: %r', labels)
        LOGGER.debug('features: %r', features)
        LOGGER.debug('training tei: %r', etree.tostring(xml_writer.root))
        assert len(texts) == 1
        assert list(texts[0]) == [TOKEN_1, TOKEN_2]
        assert list(labels[0]) == ['B-<author>', 'I-<author>']
        assert features.tolist() == expected_features.tolist()
