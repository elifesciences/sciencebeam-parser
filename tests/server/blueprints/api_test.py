from __future__ import absolute_import

from contextlib import contextmanager
import logging
import json
from io import BytesIO
from mock import patch, MagicMock, ANY

from flask import Flask
from werkzeug.exceptions import BadRequest

import pytest

from sciencebeam.utils.mime_type_constants import MimeTypes
from sciencebeam.utils.config import dict_to_config

from sciencebeam.pipelines import FieldNames

from sciencebeam.server.blueprints import api as api_module
from sciencebeam.server.blueprints.api import (
    create_api_blueprint,
    DEFAULT_FILENAME
)

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG = {}

PDF_FILENAME = 'test.pdf'
PDF_CONTENT = b'eat pdf for breakfast'
XML_CONTENT = b'<article></article>'


@contextmanager
def _api_test_client(config, args):
    blueprint = create_api_blueprint(config, args)
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    yield app.test_client()


@pytest.fixture(name='create_simple_pipeline_runner_from_config', autouse=True)
def _create_simple_pipeline_runner_from_config():
    with patch.object(api_module, 'create_simple_pipeline_runner_from_config') as \
            create_simple_pipeline_runner_from_config:

        create_simple_pipeline_runner_from_config.return_value.get_supported_types.return_value = {
            MimeTypes.PDF
        }
        yield create_simple_pipeline_runner_from_config


@pytest.fixture(name='pipeline_runner')
def _pipeline_runner(create_simple_pipeline_runner_from_config):
    return create_simple_pipeline_runner_from_config.return_value


@pytest.fixture(name='config')
def _config():
    return dict_to_config({})


@pytest.fixture(name='args')
def _args():
    return MagicMock(name='args')


def _get_json(response):
    return json.loads(response.data.decode('utf-8'))


def _get_ok_json(response):
    assert response.status_code == 200
    return _get_json(response)


class TestApiBlueprint:
    class TestInit:
        def test_should_pass_config_and_args_to_runner_factory(
                self, create_simple_pipeline_runner_from_config, config, args):

            with _api_test_client(config, args):
                create_simple_pipeline_runner_from_config.assert_called_with(
                    config, args
                )

    class TestRoot:
        def test_should_have_links(self, config, args):
            with _api_test_client(config, args) as test_client:
                response = test_client.get('/')
                assert _get_ok_json(response) == {
                    'links': {
                        'convert': '/convert'
                    }
                }

    class TestConvert:
        def test_should_show_form_on_get(self, config, args):
            with _api_test_client(config, args) as test_client:
                response = test_client.get('/convert')
                assert response.status_code == 200
                assert 'html' in str(response.data)

        def test_should_reject_post_without_data(self, config, args):
            with _api_test_client(config, args) as test_client:
                response = test_client.post('/convert')
                assert response.status_code == BadRequest.code

        def test_should_reject_post_with_empty_pdf(self, config, args):
            with _api_test_client(config, args) as test_client:
                response = test_client.post(
                    '/convert', content_type=MimeTypes.PDF
                )
                assert response.status_code == BadRequest.code

        def test_should_reject_post_with_wong_type(self, config, args):
            with _api_test_client(config, args) as test_client:
                response = test_client.post(
                    '/convert', data=PDF_CONTENT, content_type='other'
                )
                assert response.status_code == BadRequest.code

        def test_should_reject_file_with_wrong_name(self, config, args):
            with _api_test_client(config, args) as test_client:
                response = test_client.post(
                    '/convert', data=dict(
                        otherfile=(BytesIO(PDF_CONTENT), PDF_FILENAME)
                    )
                )
                assert response.status_code == BadRequest.code

        def test_should_accept_file_and_pass_to_convert_method(self, config, args, pipeline_runner):
            with _api_test_client(config, args) as test_client:
                pipeline_runner.convert.return_value = {
                    'content': XML_CONTENT,
                    'type': MimeTypes.JATS_XML
                }
                response = test_client.post('/convert', data=dict(
                    file=(BytesIO(PDF_CONTENT), PDF_FILENAME),
                ))
                expected_context = {'request_args': {}}
                pipeline_runner.convert.assert_called_with(
                    content=PDF_CONTENT, filename=PDF_FILENAME, data_type=MimeTypes.PDF,
                    includes=None,
                    context=expected_context
                )
                assert response.status_code == 200
                assert response.data == XML_CONTENT

        def test_should_accept_post_data_and_pass_to_convert_method(
                self, config, args, pipeline_runner):

            with _api_test_client(config, args) as test_client:
                pipeline_runner.convert.return_value = {
                    'content': XML_CONTENT,
                    'type': MimeTypes.JATS_XML
                }
                response = test_client.post(
                    '/convert?filename=%s' % PDF_FILENAME,
                    data=PDF_CONTENT,
                    content_type=MimeTypes.PDF
                )
                pipeline_runner.convert.assert_called_with(
                    content=PDF_CONTENT, filename=PDF_FILENAME, data_type=MimeTypes.PDF,
                    includes=None,
                    context=ANY
                )
                actual_context = pipeline_runner.convert.call_args[1]['context']
                actual_request_args = actual_context['request_args']
                assert actual_request_args.get('filename') == PDF_FILENAME
                assert response.status_code == 200
                assert response.data == XML_CONTENT

        def test_should_accept_post_data_without_filename(
                self, config, args, pipeline_runner):

            with _api_test_client(config, args) as test_client:
                pipeline_runner.convert.return_value = {
                    'content': XML_CONTENT,
                    'type': MimeTypes.JATS_XML
                }
                response = test_client.post(
                    '/convert',
                    data=PDF_CONTENT,
                    content_type=MimeTypes.PDF
                )
                expected_context = {'request_args': {}}
                pipeline_runner.convert.assert_called_with(
                    content=PDF_CONTENT,
                    filename='%s.pdf' % DEFAULT_FILENAME,
                    data_type=MimeTypes.PDF,
                    includes=None,
                    context=expected_context
                )
                assert response.status_code == 200
                assert response.data == XML_CONTENT

        def test_should_pass_includes_parameter_to_convert_method(
                self, config, args, pipeline_runner: MagicMock):

            with _api_test_client(config, args) as test_client:
                pipeline_runner.convert.return_value = {
                    'content': XML_CONTENT,
                    'type': MimeTypes.JATS_XML
                }
                includes_arg = ','.join([FieldNames.TITLE, FieldNames.ABSTRACT])
                response = test_client.post(
                    '/convert?filename=%s&includes=%s' % (
                        PDF_FILENAME, includes_arg
                    ),
                    data=PDF_CONTENT,
                    content_type=MimeTypes.PDF
                )
                pipeline_runner.convert.assert_called_with(
                    content=PDF_CONTENT, filename=PDF_FILENAME, data_type=MimeTypes.PDF,
                    includes={FieldNames.TITLE, FieldNames.ABSTRACT},
                    context=ANY
                )
                actual_context = pipeline_runner.convert.call_args[1]['context']
                actual_request_args = actual_context['request_args']
                assert actual_request_args.get('filename') == PDF_FILENAME
                assert actual_request_args.get('includes') == includes_arg
                assert response.status_code == 200
                assert response.data == XML_CONTENT
