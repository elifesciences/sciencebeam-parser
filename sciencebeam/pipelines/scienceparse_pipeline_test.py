import argparse
from functools import reduce # pylint: disable=W0622

from mock import patch, MagicMock

import pytest

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import scienceparse_pipeline as scienceparse_pipeline_module
from .scienceparse_pipeline import PIPELINE

PDF_INPUT = {
  'filename': 'test.pdf',
  'content': b'PDF insider 1',
  'type': MimeTypes.PDF
}

JSON_CONTENT = b'{title: "JSON"}'

@pytest.fixture(name='requests_post', autouse=True)
def _requests_post():
  with patch.object(scienceparse_pipeline_module, 'requests_post') as requests_post:
    yield requests_post

@pytest.fixture(name='response')
def _response(requests_post):
  return requests_post.return_value

@pytest.fixture(name='json_to_xml', autouse=True)
def _json_to_xml():
  with patch.object(scienceparse_pipeline_module, 'json_to_xml') as json_to_xml:
    yield json_to_xml

@pytest.fixture(name='xslt_transformer_from_file', autouse=True)
def _xslt_transformer_from_file():
  with patch.object(scienceparse_pipeline_module, 'xslt_transformer_from_file') \
    as xslt_transformer_from_file:

    yield xslt_transformer_from_file

@pytest.fixture(name='xslt_transformer')
def _xslt_transformer(xslt_transformer_from_file):
  return xslt_transformer_from_file.return_value

@pytest.fixture(name='ScienceParseApiStep')
def _science_parse_api_step():
  with patch.object(scienceparse_pipeline_module, 'ScienceParseApiStep') \
    as science_parse_api_step:

    yield science_parse_api_step

@pytest.fixture(name='api_step')
def _api_step(ScienceParseApiStep):
  yield ScienceParseApiStep.return_value

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

class TestScienceParsePipeline(object):
  def test_should_pass_api_url_and_pdf_content_to_requests_post_call(
    self, config, args, requests_post):

    args.science_parse_url = 'http://scienceparse/api'
    _run_pipeline(config, args, PDF_INPUT)
    requests_post.assert_called_with(
      args.science_parse_url,
      data=PDF_INPUT['content'],
      headers={'Content-Type': MimeTypes.PDF}
    )

  def test_should_return_json_content_as_xml_content_without_xslt(
    self, config, args, response):

    args.no_science_parse_xslt = True

    response.text = JSON_CONTENT
    response.headers = {'Content-Type': MimeTypes.JSON}

    result = _run_pipeline(config, args, PDF_INPUT)
    assert result['content'] == JSON_CONTENT
    assert result['type'] == MimeTypes.JSON

  def test_should_pass_xslt_path_to_xslt_transform_from_file(
    self, config, args, xslt_transformer_from_file):

    args.no_science_parse_xslt = False
    args.no_science_parse_pretty_print = False
    args.science_parse_xslt_path = '/test.xsl'
    _run_pipeline(config, args, PDF_INPUT)
    xslt_transformer_from_file.assert_called_with(args.science_parse_xslt_path, pretty_print=True)

  def test_should_return_apply_xslt_transform_to_json_to_xml_content(
    self, config, args, response, json_to_xml, xslt_transformer):

    args.no_science_parse_xslt = False

    response.text = JSON_CONTENT
    response.headers = {'Content-Type': MimeTypes.JSON}

    result = _run_pipeline(config, args, PDF_INPUT)
    xslt_transformer.assert_called_with(json_to_xml(JSON_CONTENT))
    assert result['content'] == xslt_transformer.return_value
    assert result['type'] == MimeTypes.JATS_XML

  def test_should_disable_pretty_print_xslt_output(
    self, config, args, xslt_transformer_from_file):

    args.no_science_parse_xslt = False
    args.no_science_parse_pretty_print = True
    args.science_parse_xslt_path = '/test.xsl'
    _run_pipeline(config, args, PDF_INPUT)
    xslt_transformer_from_file.assert_called_with(args.science_parse_xslt_path, pretty_print=False)
