from __future__ import absolute_import
from abc import ABC, abstractmethod

import logging
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

from flask import Flask
from flask.testing import FlaskClient
from werkzeug.exceptions import BadRequest

import pytest
from sciencebeam_parser.app.parser import (
    UnsupportedRequestMediaTypeScienceBeamParserError,
    UnsupportedResponseMediaTypeScienceBeamParserError
)

from sciencebeam_parser.config.config import AppConfig
from sciencebeam_parser.service.blueprints.api import (
    ApiBlueprint
)
from sciencebeam_parser.utils.media_types import MediaTypes
from sciencebeam_parser.resources.default_config import DEFAULT_CONFIG_FILE


LOGGER = logging.getLogger(__name__)

PDF_FILENAME_1 = 'test.pdf'
PDF_CONTENT_1 = b'test pdf content'
DOCX_CONTENT_1 = b'test docx content 1'
XML_CONTENT_1 = b'<article></article>'

TEI_XML_CONTENT_1 = b'<TEI>1</TEI>'
JATS_XML_CONTENT_1 = b'<article>1</article>'
IMAGE_DATA_1 = b'Image 1'
ZIP_CONTENT_1 = b'ZIP 1'


@pytest.fixture(name='request_temp_path')
def _request_temp_path(tmp_path: Path) -> Path:
    request_temp_path = tmp_path / 'request'
    request_temp_path.mkdir()
    return request_temp_path


@pytest.fixture(name='sciencebeam_parser_mock')
def _sciencebeam_parser_mock() -> MagicMock:
    return MagicMock(name='sciencebeam_parser')


@pytest.fixture(name='sciencebeam_parser_session_mock')
def _sciencebeam_parser_session_mock(
    sciencebeam_parser_mock: MagicMock
) -> MagicMock:
    return sciencebeam_parser_mock.get_new_session.return_value.__enter__.return_value


@pytest.fixture(name='sciencebeam_parser_source_mock')
def _sciencebeam_parser_source_mock(
    sciencebeam_parser_session_mock: MagicMock
) -> MagicMock:
    return sciencebeam_parser_session_mock.get_source.return_value


@pytest.fixture(name='get_local_file_for_response_media_type_mock')
def _get_local_file_for_response_media_type_mock(
    sciencebeam_parser_source_mock: MagicMock
) -> MagicMock:
    return sciencebeam_parser_source_mock.get_local_file_for_response_media_type


@pytest.fixture(name='app_config', scope='session')
def _app_config() -> AppConfig:
    return AppConfig.load_yaml(DEFAULT_CONFIG_FILE)


def _create_test_client(
    sciencebeam_parser_mock: MagicMock
) -> FlaskClient:
    blueprint = ApiBlueprint(sciencebeam_parser_mock)
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    return app.test_client()


@pytest.fixture(name='test_client')
def _test_client(
    sciencebeam_parser_mock: MagicMock
) -> FlaskClient:
    return _create_test_client(sciencebeam_parser_mock)


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
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path,
            post_data_key: str
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/pdfalto', data={
                post_data_key: (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            })
            assert response.status_code == 200
            assert response.data == XML_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.ALTO_XML
            )

    class _AbstractPdfConversionApiTest(ABC):
        @abstractmethod
        def get_api_path(self) -> str:
            pass

        def test_should_show_form_on_get(self, test_client: FlaskClient):
            response = test_client.get(self.get_api_path())
            assert response.status_code == 200
            assert 'html' in str(response.data)

        def test_should_reject_post_without_data(self, test_client: FlaskClient):
            response = test_client.post(self.get_api_path())
            assert response.status_code == BadRequest.code

        def test_should_reject_unsupported_request_media_type(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock
        ):
            get_local_file_for_response_media_type_mock.side_effect = (
                UnsupportedRequestMediaTypeScienceBeamParserError()
            )
            response = test_client.post(self.get_api_path(), data={
                'input': (BytesIO(PDF_CONTENT_1), 'test.unsupported')
            })
            assert response.status_code == BadRequest.code

        def test_should_reject_unsupported_accept_media_type(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock
        ):
            get_local_file_for_response_media_type_mock.side_effect = (
                UnsupportedResponseMediaTypeScienceBeamParserError()
            )
            response = test_client.post(self.get_api_path(), data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': 'media/unsupported'})
            assert response.status_code == BadRequest.code

    class TestProcessHeaderDocument(_AbstractPdfConversionApiTest):
        def get_api_path(self) -> str:
            return '/processHeaderDocument'

        @pytest.mark.parametrize(
            'post_data_key',
            ['file', 'input']
        )
        def test_should_accept_file_and_pass_to_convert_method(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path,
            post_data_key: str
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(TEI_XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/processHeaderDocument', data={
                post_data_key: (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            })
            assert response.status_code == 200
            assert response.data == TEI_XML_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.TEI_XML
            )

        def test_should_convert_to_jats(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(JATS_XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/processHeaderDocument', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': MediaTypes.JATS_XML})
            assert response.status_code == 200
            assert response.data == JATS_XML_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.JATS_XML
            )

    class TestProcessFullTextDocument(_AbstractPdfConversionApiTest):
        def get_api_path(self) -> str:
            return '/processFulltextDocument'

        @pytest.mark.parametrize(
            'post_data_key',
            ['file', 'input']
        )
        def test_should_accept_file_and_pass_to_convert_method(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path,
            post_data_key: str
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(TEI_XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/processFulltextDocument', data={
                post_data_key: (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            })
            assert response.status_code == 200
            assert response.data == TEI_XML_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.TEI_XML
            )

        def test_should_convert_to_jats(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(JATS_XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/processFulltextDocument', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': MediaTypes.JATS_XML})
            assert response.status_code == 200
            assert response.data == JATS_XML_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.JATS_XML
            )

    class TestProcessReferences(_AbstractPdfConversionApiTest):
        def get_api_path(self) -> str:
            return '/processReferences'

        @pytest.mark.parametrize(
            'post_data_key',
            ['file', 'input']
        )
        def test_should_accept_file_and_pass_to_convert_method(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path,
            post_data_key: str
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(TEI_XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/processReferences', data={
                post_data_key: (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            })
            assert response.status_code == 200
            assert response.data == TEI_XML_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.TEI_XML
            )

        def test_should_convert_to_jats(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(JATS_XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/processReferences', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': MediaTypes.JATS_XML})
            assert response.status_code == 200
            assert response.data == JATS_XML_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.JATS_XML
            )

    class TestProcessFullTextAssetDocument(_AbstractPdfConversionApiTest):
        def get_api_path(self) -> str:
            return '/processFulltextAssetDocument'

        @pytest.mark.parametrize(
            'post_data_key',
            ['file', 'input']
        )
        def test_should_accept_file_and_pass_to_convert_method(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path,
            post_data_key: str
        ):
            expected_output_path = request_temp_path / 'result.zip'
            expected_output_path.write_bytes(ZIP_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/processFulltextAssetDocument', data={
                post_data_key: (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            })
            assert response.status_code == 200
            assert response.content_type == 'application/zip'
            assert response.data == ZIP_CONTENT_1

        def test_should_convert_to_jats(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'result.zip'
            expected_output_path.write_bytes(ZIP_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/processFulltextAssetDocument', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': MediaTypes.JATS_ZIP})
            assert response.status_code == 200
            assert response.content_type == 'application/zip'
            assert response.data == ZIP_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.JATS_ZIP
            )

    class TestProcessConvert(_AbstractPdfConversionApiTest):
        def get_api_path(self) -> str:
            return '/convert'

        def test_should_convert_to_jats_by_default(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(JATS_XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/convert', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            })
            assert response.status_code == 200
            assert response.data == JATS_XML_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.JATS_XML
            )

        def test_should_return_tei_xml_if_requested(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(TEI_XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/convert', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': MediaTypes.TEI_XML})
            assert response.status_code == 200
            assert response.data == TEI_XML_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.TEI_XML
            )

        def test_should_be_able_to_request_jats_zip(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'result.zip'
            expected_output_path.write_bytes(ZIP_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/convert', data={
                'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)
            }, headers={'Accept': MediaTypes.JATS_ZIP})
            assert response.status_code == 200
            assert response.content_type == 'application/zip'
            assert response.data == ZIP_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.JATS_ZIP
            )

        def test_should_be_able_to_pass_includes_request_arg(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(JATS_XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post(
                '/convert',
                data={'input': (BytesIO(PDF_CONTENT_1), PDF_FILENAME_1)},
                headers={'Accept': MediaTypes.JATS_XML},
                query_string='includes=title'
            )
            assert response.status_code == 200
            assert response.data == JATS_XML_CONTENT_1

        def test_should_accept_docx(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(JATS_XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post(
                '/convert',
                data={'input': (BytesIO(DOCX_CONTENT_1), 'test.docx')},
                headers={'Accept': MediaTypes.JATS_XML},
                query_string='includes=title'
            )
            assert response.status_code == 200
            assert response.data == JATS_XML_CONTENT_1

        def test_should_convert_docx_to_pdf(
            self,
            test_client: FlaskClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_output_path = request_temp_path / 'test.pdf'
            expected_output_path.write_bytes(PDF_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post(
                '/convert',
                data={'input': (BytesIO(DOCX_CONTENT_1), 'test.docx')},
                headers={'Accept': MediaTypes.PDF}
            )
            assert response.status_code == 200
            assert response.data == PDF_CONTENT_1
