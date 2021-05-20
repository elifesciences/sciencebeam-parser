from __future__ import absolute_import

import logging
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Iterator

from flask import Flask
from flask.testing import FlaskClient
from werkzeug.exceptions import BadRequest

import pytest

from pygrobid.external.pdfalto.wrapper import PdfAltoWrapper

from pygrobid.service.blueprints import api as api_module
from pygrobid.service.blueprints.api import (
    ApiBlueprint
)


LOGGER = logging.getLogger(__name__)

PDF_FILENAME_1 = 'test.pdf'
PDF_CONTENT_1 = b'test pdf content'
XML_CONTENT_1 = b'<article></article>'


@pytest.fixture(name='request_temp_path')
def _request_temp_path(tmp_path: Path) -> Iterator[Path]:
    request_temp_path = tmp_path / 'request'
    request_temp_path.mkdir()
    with patch.object(api_module, 'TemporaryDirectory') as mock:
        mock.return_value.__enter__.return_value = request_temp_path
        yield request_temp_path


@pytest.fixture(name='pdfalto_wrapper_get_mock')
def _pdfalto_wrapper_get_mock() -> Iterator[MagicMock]:
    with patch.object(PdfAltoWrapper, 'get') as mock:
        mock.return_value = MagicMock(name='PdfAltoWrapper')
        yield mock


@pytest.fixture(name='pdfalto_wrapper_mock', autouse=True)
def _pdfalto_wrapper_mock(pdfalto_wrapper_get_mock: MagicMock) -> MagicMock:
    return pdfalto_wrapper_get_mock.return_value


@pytest.fixture(name='test_client')
def _test_client() -> Iterator[FlaskClient]:
    blueprint = ApiBlueprint()
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
        def test_should_have_links(self, test_client):
            response = test_client.get('/')
            assert _get_ok_json(response) == {
                'links': {
                    'pdfalto': '/pdfalto'
                }
            }

    class TestPdfAlto:
        def test_should_show_form_on_get(self, test_client):
            response = test_client.get('/pdfalto')
            assert response.status_code == 200
            assert 'html' in str(response.data)

        def test_should_reject_post_without_data(self, test_client):
            response = test_client.post('/pdfalto')
            assert response.status_code == BadRequest.code

        def test_should_accept_file_and_pass_to_convert_method(
            self,
            test_client,
            pdfalto_wrapper_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_pdf_path = request_temp_path / 'test.pdf'
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            response = test_client.post('/pdfalto', data=dict(
                file=(BytesIO(PDF_CONTENT_1), PDF_FILENAME_1),
            ))
            pdfalto_wrapper_mock.convert_pdf_to_pdfalto_xml.assert_called_with(
                str(expected_pdf_path),
                str(expected_output_path),
                first_page=None,
                last_page=None
            )
            assert response.status_code == 200
            assert response.data == XML_CONTENT_1

        def test_should_accept_file_as_input_name_and_pass_to_convert_method(
            self,
            test_client,
            pdfalto_wrapper_mock: MagicMock,
            request_temp_path: Path
        ):
            expected_pdf_path = request_temp_path / 'test.pdf'
            expected_output_path = request_temp_path / 'test.lxml'
            expected_output_path.write_bytes(XML_CONTENT_1)
            response = test_client.post('/pdfalto', data=dict(
                input=(BytesIO(PDF_CONTENT_1), PDF_FILENAME_1),
            ))
            pdfalto_wrapper_mock.convert_pdf_to_pdfalto_xml.assert_called_with(
                str(expected_pdf_path),
                str(expected_output_path),
                first_page=None,
                last_page=None
            )
            assert response.status_code == 200
            assert response.data == XML_CONTENT_1
