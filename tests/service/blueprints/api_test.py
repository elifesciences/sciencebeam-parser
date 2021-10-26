from __future__ import absolute_import

import logging
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Iterator
from zipfile import ZipFile

from flask import Flask
from flask.testing import FlaskClient
from werkzeug.exceptions import BadRequest
from lxml import etree

import pytest

from sciencebeam_parser.config.config import AppConfig, DEFAULT_CONFIG_PATH
from sciencebeam_parser.document.layout_document import LayoutGraphic
from sciencebeam_parser.document.semantic_document import SemanticDocument, SemanticGraphic
from sciencebeam_parser.document.tei.document import TeiDocument
from sciencebeam_parser.service.blueprints import api as api_module
from sciencebeam_parser.service.blueprints.api import (
    ApiBlueprint
)
from sciencebeam_parser.utils.media_types import MediaTypes


LOGGER = logging.getLogger(__name__)

PDF_FILENAME_1 = 'test.pdf'
PDF_CONTENT_1 = b'test pdf content'
XML_CONTENT_1 = b'<article></article>'

TEI_XML_CONTENT_1 = b'<TEI>1</TEI>'
JATS_XML_CONTENT_1 = b'<article>1</article>'
IMAGE_DATA_1 = b'Image 1'


@pytest.fixture(name='request_temp_path')
def _request_temp_path(tmp_path: Path) -> Iterator[Path]:
    request_temp_path = tmp_path / 'request'
    request_temp_path.mkdir()
    with patch.object(api_module, 'TemporaryDirectory') as mock:
        mock.return_value.__enter__.return_value = request_temp_path
        yield request_temp_path


@pytest.fixture(name='download_manager_class_mock', autouse=True)
def _download_manager_class_mock() -> Iterator[MagicMock]:
    with patch.object(api_module, 'DownloadManager') as mock:
        yield mock


@pytest.fixture(name='pdfalto_wrapper_class_mock')
def _pdfalto_wrapper_class_mock() -> Iterator[MagicMock]:
    with patch.object(api_module, 'PdfAltoWrapper') as mock:
        yield mock


@pytest.fixture(name='pdfalto_wrapper_mock', autouse=True)
def _pdfalto_wrapper_mock(pdfalto_wrapper_class_mock: MagicMock) -> MagicMock:
    return pdfalto_wrapper_class_mock.return_value


@pytest.fixture(name='full_text_processor_class_mock')
def _fulltextprocessor_class_mock() -> Iterator[MagicMock]:
    with patch.object(api_module, 'FullTextProcessor') as mock:
        yield mock


@pytest.fixture(name='full_text_processor_mock', autouse=True)
def _fulltextprocessor_mock(full_text_processor_class_mock: MagicMock) -> MagicMock:
    return full_text_processor_class_mock.return_value


@pytest.fixture(name='load_models_mock', autouse=True)
def _load_models_mock() -> Iterator[MagicMock]:
    with patch.object(api_module, 'load_models') as mock:
        yield mock


@pytest.fixture(name='get_tei_for_semantic_document_mock', autouse=True)
def _get_tei_for_semantic_document_mock() -> Iterator[MagicMock]:
    with patch.object(api_module, 'get_tei_for_semantic_document') as mock:
        yield mock


@pytest.fixture(name='load_app_features_context_mock', autouse=True)
def _load_app_features_context_mock() -> Iterator[MagicMock]:
    with patch.object(api_module, 'load_app_features_context') as mock:
        yield mock


@pytest.fixture(name='xslt_transformer_wrapper_class_mock', autouse=True)
def _xslt_transformer_wrapper_class_mock() -> Iterator[MagicMock]:
    with patch.object(api_module, 'XsltTransformerWrapper') as mock:
        yield mock


@pytest.fixture(name='xslt_transformer_wrapper_mock')
def _xslt_transformer_wrapper_mock(
    xslt_transformer_wrapper_class_mock: MagicMock
) -> MagicMock:
    return xslt_transformer_wrapper_class_mock.from_template_file.return_value


@pytest.fixture(name='app_config', scope='session')
def _app_config() -> AppConfig:
    return AppConfig.load_yaml(DEFAULT_CONFIG_PATH)


@pytest.fixture(name='test_client')
def _test_client(app_config: AppConfig) -> Iterator[FlaskClient]:
    blueprint = ApiBlueprint(app_config)
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    yield app.test_client()


def _get_json(response):
    return json.loads(response.data.decode('utf-8'))


def _get_ok_json(response):
    assert response.status_code == 200
    return _get_json(response)


class TestApiBlueprint:
    class TestRoot:
        def test_should_have_links(self, test_client: FlaskClient):
            response = test_client.get('/')
            assert _get_ok_json(response) == {
                'links': {
                    'pdfalto': '/pdfalto'
                }
            }

    class TestPdfAlto:
        def test_should_show_form_on_get(self, test_client: FlaskClient):
            response = test_client.get('/pdfalto')
            assert response.status_code == 200
            assert 'html' in str(response.data)

        def test_should_reject_post_without_data(self, test_client: FlaskClient):
            response = test_client.post('/pdfalto')
            assert response.status_code == BadRequest.code

        @pytest.mark.parametrize(
            'post_data_key',
            ['file', 'input']
        )
        def test_should_accept_file_and_pass_to_convert_method(
            self,
            test_client: FlaskClient,
            pdfalto_wrapper_mock: MagicMock,
            request_temp_path: Path,
            post_data_key: str
        ):
            expected_pdf_path = request_temp_path / 'test.pdf'
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            response = test_client.post('/pdfalto', data={
                post_data_key: (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            })
            pdfalto_wrapper_mock.convert_pdf_to_pdfalto_xml.assert_called_with(
                str(expected_pdf_path),
                str(expected_output_path),
                first_page=None,
                last_page=None
            )
            assert response.status_code == 200
            assert response.data == XML_CONTENT_1

    class TestProcessHeaderDocument:
        def test_should_show_form_on_get(self, test_client: FlaskClient):
            response = test_client.get('/processHeaderDocument')
            assert response.status_code == 200
            assert 'html' in str(response.data)

        def test_should_reject_post_without_data(self, test_client: FlaskClient):
            response = test_client.post('/processHeaderDocument')
            assert response.status_code == BadRequest.code

        @pytest.mark.parametrize(
            'post_data_key',
            ['file', 'input']
        )
        def test_should_accept_file_and_pass_to_convert_method(
            self,
            test_client: FlaskClient,
            pdfalto_wrapper_mock: MagicMock,
            get_tei_for_semantic_document_mock: MagicMock,
            request_temp_path: Path,
            post_data_key: str
        ):
            expected_pdf_path = request_temp_path / 'test.pdf'
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            response = test_client.post('/processHeaderDocument', data={
                post_data_key: (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            })
            pdfalto_wrapper_mock.convert_pdf_to_pdfalto_xml.assert_called_with(
                str(expected_pdf_path),
                str(expected_output_path),
                first_page=None,
                last_page=None
            )
            assert response.status_code == 200
            assert response.data == TEI_XML_CONTENT_1

        def test_should_convert_to_jats(
            self,
            test_client: FlaskClient,
            get_tei_for_semantic_document_mock: MagicMock,
            xslt_transformer_wrapper_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            xslt_transformer_wrapper_mock.return_value = (
                etree.fromstring(JATS_XML_CONTENT_1)
            )
            response = test_client.post('/processHeaderDocument', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': MediaTypes.JATS_XML})
            assert response.status_code == 200
            assert response.data == JATS_XML_CONTENT_1

        def test_should_reject_unsupported_accept_media_type(
            self,
            test_client: FlaskClient,
            get_tei_for_semantic_document_mock: MagicMock
        ):
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            response = test_client.post('/processHeaderDocument', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': 'media/unsupported'})
            assert response.status_code == 400

    class TestProcessFullTextDocument:
        def test_should_show_form_on_get(self, test_client: FlaskClient):
            response = test_client.get('/processFulltextDocument')
            assert response.status_code == 200
            assert 'html' in str(response.data)

        def test_should_reject_post_without_data(self, test_client: FlaskClient):
            response = test_client.post('/processFulltextDocument')
            assert response.status_code == BadRequest.code

        @pytest.mark.parametrize(
            'post_data_key',
            ['file', 'input']
        )
        def test_should_accept_file_and_pass_to_convert_method(
            self,
            test_client: FlaskClient,
            pdfalto_wrapper_mock: MagicMock,
            get_tei_for_semantic_document_mock: MagicMock,
            request_temp_path: Path,
            post_data_key: str
        ):
            expected_pdf_path = request_temp_path / 'test.pdf'
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            response = test_client.post('/processFulltextDocument', data={
                post_data_key: (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            })
            pdfalto_wrapper_mock.convert_pdf_to_pdfalto_xml.assert_called_with(
                str(expected_pdf_path),
                str(expected_output_path),
                first_page=None,
                last_page=None
            )
            assert response.status_code == 200
            assert response.data == TEI_XML_CONTENT_1

        def test_should_convert_to_jats(
            self,
            test_client: FlaskClient,
            get_tei_for_semantic_document_mock: MagicMock,
            xslt_transformer_wrapper_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            xslt_transformer_wrapper_mock.return_value = (
                etree.fromstring(JATS_XML_CONTENT_1)
            )
            response = test_client.post('/processFulltextDocument', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': MediaTypes.JATS_XML})
            assert response.status_code == 200
            assert response.data == JATS_XML_CONTENT_1

        def test_should_reject_unsupported_accept_media_type(
            self,
            test_client: FlaskClient,
            get_tei_for_semantic_document_mock: MagicMock
        ):
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            response = test_client.post('/processFulltextDocument', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': 'media/unsupported'})
            assert response.status_code == 400

    class TestProcessFullTextAssetDocument:
        def test_should_show_form_on_get(self, test_client: FlaskClient):
            response = test_client.get('/processFulltextAssetDocument')
            assert response.status_code == 200
            assert 'html' in str(response.data)

        def test_should_reject_post_without_data(self, test_client: FlaskClient):
            response = test_client.post('/processFulltextAssetDocument')
            assert response.status_code == BadRequest.code

        @pytest.mark.parametrize(
            'post_data_key',
            ['file', 'input']
        )  # pylint: disable=too-many-locals
        def test_should_accept_file_and_pass_to_convert_method(
            self,
            test_client: FlaskClient,
            pdfalto_wrapper_mock: MagicMock,
            full_text_processor_mock: MagicMock,
            get_tei_for_semantic_document_mock: MagicMock,
            request_temp_path: Path,
            post_data_key: str
        ):
            expected_pdf_path = request_temp_path / 'test.pdf'
            expected_output_path = request_temp_path / 'test.lxml'
            graphic_local_file_path = request_temp_path / 'image1.png'
            graphic_relative_path = graphic_local_file_path.name
            expected_output_path.write_bytes(XML_CONTENT_1)
            graphic_local_file_path.write_bytes(IMAGE_DATA_1)
            semantic_document = SemanticDocument()
            semantic_document.back_section.add_content(
                SemanticGraphic(
                    layout_graphic=LayoutGraphic(
                        local_file_path=str(graphic_local_file_path)
                    ),
                    relative_path=graphic_relative_path
                )
            )
            full_text_processor_mock.get_semantic_document_for_layout_document.return_value = (
                semantic_document
            )
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            response = test_client.post('/processFulltextAssetDocument', data={
                post_data_key: (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            })
            pdfalto_wrapper_mock.convert_pdf_to_pdfalto_xml.assert_called_with(
                str(expected_pdf_path),
                str(expected_output_path),
                first_page=None,
                last_page=None
            )
            assert response.status_code == 200
            assert response.content_type == 'application/zip'
            with ZipFile(BytesIO(response.data), 'r') as zip_file:
                tei_xml_data = zip_file.read('tei.xml')
                assert tei_xml_data == TEI_XML_CONTENT_1
                image_data = zip_file.read(graphic_relative_path)
                assert image_data == IMAGE_DATA_1

        def test_should_convert_to_jats(
            self,
            test_client: FlaskClient,
            get_tei_for_semantic_document_mock: MagicMock,
            xslt_transformer_wrapper_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            xslt_transformer_wrapper_mock.return_value = (
                etree.fromstring(JATS_XML_CONTENT_1)
            )
            response = test_client.post('/processFulltextAssetDocument', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': MediaTypes.JATS_ZIP})
            assert response.status_code == 200
            assert response.content_type == 'application/zip'
            with ZipFile(BytesIO(response.data), 'r') as zip_file:
                tei_xml_data = zip_file.read('jats.xml')
                assert tei_xml_data == JATS_XML_CONTENT_1

        def test_should_reject_unsupported_accept_media_type(
            self,
            test_client: FlaskClient,
            get_tei_for_semantic_document_mock: MagicMock
        ):
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            response = test_client.post('/processFulltextAssetDocument', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': 'media/unsupported'})
            assert response.status_code == 400

    class TestProcessConvert:
        def test_should_show_form_on_get(self, test_client: FlaskClient):
            response = test_client.get('/convert')
            assert response.status_code == 200
            assert 'html' in str(response.data)

        def test_should_reject_post_without_data(self, test_client: FlaskClient):
            response = test_client.post('/convert')
            assert response.status_code == BadRequest.code

        def test_should_convert_to_jats_by_default(
            self,
            test_client: FlaskClient,
            get_tei_for_semantic_document_mock: MagicMock,
            xslt_transformer_wrapper_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            xslt_transformer_wrapper_mock.return_value = (
                etree.fromstring(JATS_XML_CONTENT_1)
            )
            response = test_client.post('/convert', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            })
            assert response.status_code == 200
            assert response.data == JATS_XML_CONTENT_1

        def test_should_return_tei_xml_if_requested(
            self,
            test_client: FlaskClient,
            get_tei_for_semantic_document_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            response = test_client.post('/convert', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': MediaTypes.TEI_XML})
            assert response.status_code == 200
            assert response.data == TEI_XML_CONTENT_1

        def test_should_be_able_to_request_jats_zip(
            self,
            test_client: FlaskClient,
            get_tei_for_semantic_document_mock: MagicMock,
            xslt_transformer_wrapper_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            xslt_transformer_wrapper_mock.return_value = (
                etree.fromstring(JATS_XML_CONTENT_1)
            )
            response = test_client.post('/convert', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': MediaTypes.JATS_ZIP})
            assert response.status_code == 200
            assert response.content_type == 'application/zip'
            with ZipFile(BytesIO(response.data), 'r') as zip_file:
                tei_xml_data = zip_file.read('jats.xml')
                assert tei_xml_data == JATS_XML_CONTENT_1

        def test_should_reject_unsupported_accept_media_type(
            self,
            test_client: FlaskClient,
            get_tei_for_semantic_document_mock: MagicMock
        ):
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            response = test_client.post('/convert', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': 'media/unsupported'})
            assert response.status_code == 400

        def test_should_be_able_to_pass_includes_request_arg(
            self,
            test_client: FlaskClient,
            get_tei_for_semantic_document_mock: MagicMock,
            xslt_transformer_wrapper_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            get_tei_for_semantic_document_mock.return_value = (
                TeiDocument(etree.fromstring(TEI_XML_CONTENT_1))
            )
            xslt_transformer_wrapper_mock.return_value = (
                etree.fromstring(JATS_XML_CONTENT_1)
            )
            response = test_client.post(
                '/convert',
                data={'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)},
                headers={'Accept': MediaTypes.JATS_XML},
                query_string='includes=title'
            )
            assert response.status_code == 200
            assert response.data == JATS_XML_CONTENT_1
