import logging
from configparser import ConfigParser
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam.transformers import convert_doc as convert_doc_module
from sciencebeam.transformers.convert_doc import (
    DEFAULT_DOC_CONVERT_PROCESS_TIMEOUT,
    DEFAULT_DOC_CONVERT_MAX_UPTIME,
    DOC_CONVERT_SECTION_NAME,
    AppConfigOptions,
    EnvironmentVariables,
    _get_default_config,
    _convert_doc_to,
    doc_to_pdf,
    doc_to_docx
)


LOGGER = logging.getLogger(__name__)


DOC_CONTENT_1 = b'doc content 1'
PDF_CONTENT_1 = b'pdf content 1'
DOCX_CONTENT_1 = b'docx content 1'


@pytest.fixture(name='get_doc_converter_mock', autouse=True)
def _get_doc_converter_mock():
    with patch.object(convert_doc_module, '_get_doc_converter') as m:
        yield m


@pytest.fixture(name='pdf_path')
def _pdf_path(temp_dir: Path):
    return temp_dir.joinpath('temp.pdf')


@pytest.fixture(name='doc_converter_mock', autouse=True)
def _doc_converter_mock(get_doc_converter_mock: MagicMock, pdf_path: Path):
    doc_converter_mock = get_doc_converter_mock.return_value
    doc_converter_mock.convert.return_value = str(pdf_path)
    return doc_converter_mock


@pytest.fixture(name='TemporaryDirectory_mock', autouse=True)
def _mock_temp_directory(tmpdir):
    with patch.object(convert_doc_module, 'TemporaryDirectory') as m:
        m.return_value.__enter__.return_value = str(tmpdir)
        yield m


@pytest.fixture(name='get_app_config_mock')
def _get_app_config_mock():
    with patch.object(convert_doc_module, 'get_app_config') as m:
        m.return_value = ConfigParser()
        yield m


@pytest.fixture(name='app_config_mock')
def _app_config_mock(get_app_config_mock: MagicMock) -> ConfigParser:
    return get_app_config_mock.return_value


class TestGetDefaultConfig:
    @patch('os.environ', {})
    def test_should_load_config_from_app_config(self, app_config_mock: ConfigParser):
        app_config_mock.read_dict({
            DOC_CONVERT_SECTION_NAME: {
                AppConfigOptions.PROCESS_TIMEOUT: '123',
                AppConfigOptions.MAX_UPTIME: '101',
                AppConfigOptions.STOP_LISTENER_ON_ERROR: 'true',
                AppConfigOptions.ENABLE_DEBUG: 'true'
            }
        })
        config = _get_default_config()
        LOGGER.debug('config: %s', config)
        assert config.get('process_timeout') == 123
        assert config.get('max_uptime') == 101
        assert config.get('stop_listener_on_error') is True
        assert config.get('enable_debug') is True

    @patch('os.environ', {
        EnvironmentVariables.DOC_CONVERT_PROCESS_TIMEOUT: '123',
        EnvironmentVariables.DOC_CONVERT_MAX_UPTIME: '101'
    })
    def test_should_load_config_from_env(self, app_config_mock: ConfigParser):
        app_config_mock.read_dict({
            DOC_CONVERT_SECTION_NAME: {
                AppConfigOptions.PROCESS_TIMEOUT: '1',
                AppConfigOptions.MAX_UPTIME: '1',
                AppConfigOptions.STOP_LISTENER_ON_ERROR: 'true',
                AppConfigOptions.ENABLE_DEBUG: 'true'
            }
        })
        config = _get_default_config()
        LOGGER.debug('config: %s', config)
        assert config.get('process_timeout') == 123
        assert config.get('max_uptime') == 101

    @patch('os.environ', {})
    def test_should_use_defaults(self, app_config_mock: ConfigParser):
        app_config_mock.read_dict({
            DOC_CONVERT_SECTION_NAME: {
                AppConfigOptions.STOP_LISTENER_ON_ERROR: 'true',
                AppConfigOptions.ENABLE_DEBUG: 'true'
            }
        })
        config = _get_default_config()
        LOGGER.debug('config: %s', config)
        assert config.get('process_timeout') == DEFAULT_DOC_CONVERT_PROCESS_TIMEOUT
        assert config.get('max_uptime') == DEFAULT_DOC_CONVERT_MAX_UPTIME


class TestConvertDocTo:
    def test_should_return_pdf(self, pdf_path: Path):
        pdf_path.write_bytes(PDF_CONTENT_1)
        assert _convert_doc_to(
            DOC_CONTENT_1, MimeTypes.DOC, 'pdf'
        ) == PDF_CONTENT_1

    def test_should_call_convert_with_doc(
            self, temp_dir: Path, pdf_path: Path, doc_converter_mock: MagicMock):
        pdf_path.write_bytes(PDF_CONTENT_1)
        _convert_doc_to(DOC_CONTENT_1, MimeTypes.DOC, 'pdf')
        doc_converter_mock.convert.assert_called_with(
            str(temp_dir.joinpath('temp.doc')),
            output_type='pdf'
        )

    def test_should_call_check_output_with_docx(
            self, temp_dir: Path, pdf_path: Path, doc_converter_mock: MagicMock):
        pdf_path.write_bytes(PDF_CONTENT_1)
        _convert_doc_to(DOC_CONTENT_1, MimeTypes.DOCX, 'pdf')
        doc_converter_mock.convert.assert_called_with(
            str(temp_dir.joinpath('temp.docx')),
            output_type='pdf'
        )

    def test_should_call_check_output_with_dotx(
            self, temp_dir: Path, pdf_path: Path, doc_converter_mock: MagicMock):
        pdf_path.write_bytes(PDF_CONTENT_1)
        _convert_doc_to(DOC_CONTENT_1, MimeTypes.DOTX, 'pdf')
        doc_converter_mock.convert.assert_called_with(
            str(temp_dir.joinpath('temp.dotx')),
            output_type='pdf'
        )

    def test_should_call_check_output_with_rtf(
            self, temp_dir: Path, pdf_path: Path, doc_converter_mock: MagicMock):
        pdf_path.write_bytes(PDF_CONTENT_1)
        _convert_doc_to(DOC_CONTENT_1, MimeTypes.RTF, 'pdf')
        doc_converter_mock.convert.assert_called_with(
            str(temp_dir.joinpath('temp.rtf')),
            output_type='pdf'
        )


class TestDocToPdf:
    def test_should_return_pdf(self, pdf_path: Path):
        pdf_path.write_bytes(PDF_CONTENT_1)
        assert doc_to_pdf(DOC_CONTENT_1, MimeTypes.DOC) == PDF_CONTENT_1


class TestDocToDocx:
    def test_should_return_docx(self, temp_dir: Path, doc_converter_mock: MagicMock):
        docx_path = temp_dir.joinpath('temp.docx')
        doc_converter_mock.convert.return_value = str(docx_path)
        docx_path.write_bytes(DOCX_CONTENT_1)
        assert doc_to_docx(DOC_CONTENT_1, MimeTypes.DOC) == DOCX_CONTENT_1
