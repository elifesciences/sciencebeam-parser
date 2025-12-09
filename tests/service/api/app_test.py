from io import BytesIO
import logging
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
import httpx
import pytest

from sciencebeam_parser.config.config import AppConfig
from sciencebeam_parser.resources.default_config import DEFAULT_CONFIG_FILE
from sciencebeam_parser.service.api.app import create_api_app
from sciencebeam_parser.utils.media_types import MediaTypes


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
    mock = MagicMock(
        name='sciencebeam_parser_mock'
    )
    return mock


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


def create_test_client(
    sciencebeam_parser_mock: MagicMock
) -> TestClient:
    app = create_api_app(
        sciencebeam_parser=sciencebeam_parser_mock
    )
    client = TestClient(app)
    return client


@pytest.fixture(name='test_client')
def _test_client(
    sciencebeam_parser_mock: MagicMock
) -> TestClient:
    return create_test_client(
        sciencebeam_parser_mock=sciencebeam_parser_mock
    )


def _get_ok_json(response: httpx.Response) -> dict:
    assert response.status_code == 200
    return response.json()


class TestApiApp:
    class TestRoot:
        def test_should_not_fail(self, test_client: TestClient):
            response = test_client.get('/')
            assert _get_ok_json(response)

    class TestPdfAlto:
        def test_should_reject_post_without_data(
            self,
            test_client: TestClient
        ):
            response = test_client.post('/pdfalto')
            assert response.status_code == 400

        @pytest.mark.parametrize(
            'post_data_key',
            ['file', 'input']
        )
        def test_should_accept_file_and_pass_to_convert_method(
            self,
            test_client: TestClient,
            get_local_file_for_response_media_type_mock: MagicMock,
            request_temp_path: Path,
            post_data_key: str
        ):
            expected_output_path = request_temp_path / 'result.xml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            get_local_file_for_response_media_type_mock.return_value = str(expected_output_path)
            response = test_client.post('/pdfalto', files={
                post_data_key: (PDF_FILENAME_1, BytesIO(PDF_CONTENT_1), 'application/pdf')
            })
            assert response.status_code == 200
            assert response.content == XML_CONTENT_1
            get_local_file_for_response_media_type_mock.assert_called_with(
                MediaTypes.ALTO_XML
            )
