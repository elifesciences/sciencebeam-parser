from __future__ import absolute_import

from contextlib import contextmanager
import logging
import json
from io import BytesIO
from mock import patch, MagicMock

from flask import Flask
from werkzeug.exceptions import BadRequest

import pytest

from sciencebeam.utils.config import dict_to_config

from . import api as api_module
from .api import create_api_blueprint

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

    yield create_simple_pipeline_runner_from_config

@pytest.fixture(name='pipeline_runner')
def _pipeline_runner(create_simple_pipeline_runner_from_config):
  return create_simple_pipeline_runner_from_config.return_value

@pytest.fixture(name='config')
def _config():
  return MagicMock(name='config')

@pytest.fixture(name='args')
def _args():
  return MagicMock(name='args')

def _get_json(response):
  return json.loads(response.data.decode('utf-8'))

def _get_ok_json(response):
  assert response.status_code == 200
  return _get_json(response)

def setup_module():
  logging.basicConfig(level='DEBUG')

class TestApiBlueprint(object):
  class TestInit(object):
    def test_should_pass_config_and_args_to_runner_factory(
      self, create_simple_pipeline_runner_from_config, config, args):

      with _api_test_client(config, args):
        create_simple_pipeline_runner_from_config.assert_called_with(config, args)

  class TestRoot(object):
    def test_should_have_links(self, config, args):
      with _api_test_client(config, args) as test_client:
        response = test_client.get('/')
        assert _get_ok_json(response) == {
          'links': {}
        }

  class TestConvert(object):
    def test_should_show_form_on_get(self, config, args):
      with _api_test_client(config, args) as test_client:
        response = test_client.get('/convert')
        assert response.status_code == 200
        assert 'html' in response.data

    def test_should_reject_post_without_file(self, config, args):
      with _api_test_client(config, args) as test_client:
        response = test_client.post('/convert')
        assert response.status_code == BadRequest.code

    def test_should_accept_file_and_pass_to_convert_method(self, config, args, pipeline_runner):
      with _api_test_client(config, args) as test_client:
        pipeline_runner.convert.return_value = {
          'xml_content': XML_CONTENT
        }
        response = test_client.post('/convert', data=dict(
          file=(BytesIO(PDF_CONTENT), PDF_FILENAME),
        ))
        pipeline_runner.convert.assert_called_with(
          pdf_content=PDF_CONTENT, pdf_filename=PDF_FILENAME
        )
        assert response.status_code == 200
        assert response.data == XML_CONTENT
