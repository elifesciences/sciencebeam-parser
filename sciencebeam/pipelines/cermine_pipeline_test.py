import argparse
from functools import reduce # pylint: disable=W0622

from mock import patch, MagicMock

import pytest

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import cermine_pipeline as cermine_pipeline_module
from .cermine_pipeline import PIPELINE

PDF_INPUT = {
  'filename': 'test.pdf',
  'content': b'PDF insider 1',
  'type': MimeTypes.PDF
}

XML_CONTENT = b'<XML>XML</XML>'

@pytest.fixture(name='requests_post', autouse=True)
def _requests_post():
  with patch.object(cermine_pipeline_module, 'requests_post') as requests_post:
    yield requests_post

@pytest.fixture(name='response')
def _response(requests_post):
  return requests_post.return_value

@pytest.fixture(name='CermineApiStep')
def _cermine_api_step():
  with patch.object(cermine_pipeline_module, 'CermineApiStep') \
    as cermine_api_step:

    yield cermine_api_step

@pytest.fixture(name='api_step')
def _api_step(CermineApiStep):
  yield CermineApiStep.return_value

@pytest.fixture(name='config')
def _config():
  return MagicMock(name='config')

@pytest.fixture(name='args')
def _args():
  return MagicMock(name='args')

def _run_pipeline(config, args, pdf_input):
  parser = argparse.ArgumentParser()
  PIPELINE.add_arguments(parser, config)
  steps = PIPELINE.get_steps(config, args)
  return reduce(lambda value, step: step(value), steps, pdf_input)

class TestCerminePipeline(object):
  def test_should_pass_api_url_and_pdf_content_to_requests_post_call(
    self, config, args, requests_post):

    args.cermine_url = 'http://cerminee/api'
    _run_pipeline(config, args, PDF_INPUT)
    requests_post.assert_called_with(
      args.cermine_url,
      data=PDF_INPUT['content'],
      headers={'Content-Type': MimeTypes.PDF}
    )

  def test_should_return_xml_response(
    self, config, args, response):

    args.no_science_parse_xslt = True

    response.text = XML_CONTENT
    response.headers = {'Content-Type': MimeTypes.XML}

    result = _run_pipeline(config, args, PDF_INPUT)
    assert result['content'] == XML_CONTENT
    assert result['type'] == MimeTypes.XML
