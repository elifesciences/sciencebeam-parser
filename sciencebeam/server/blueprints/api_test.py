from __future__ import absolute_import

from contextlib import contextmanager
import logging
import json

from flask import Flask

from .api import create_api_blueprint

LOGGER = logging.getLogger(__name__)

@contextmanager
def _api_test_client(args):
  blueprint = create_api_blueprint(args)
  app = Flask(__name__)
  app.register_blueprint(blueprint)
  yield app.test_client()

def _get_json(response):
  return json.loads(response.data.decode('utf-8'))

def _get_ok_json(response):
  assert response.status_code == 200
  return _get_json(response)

class TestApiBlueprint(object):
  class TestRoot(object):
    def test_should_have_links(self):
      with _api_test_client(None) as test_client:
        response = test_client.get('/')
        assert _get_ok_json(response) == {
          'links': {}
        }
