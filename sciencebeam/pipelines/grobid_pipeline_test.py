import argparse
from functools import reduce # pylint: disable=W0622

from mock import patch, MagicMock

import pytest

from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam_utils.utils.collection import extend_dict

from . import FieldNames, StepDataProps
from . import grobid_pipeline as grobid_pipeline_module
from .grobid_pipeline import (
  PIPELINE,
  LOCAL_GROBID_API_URL,
  GrobidApiPaths
)

PDF_INPUT = {
  'filename': 'test.pdf',
  'content': b'PDF insider 1',
  'type': MimeTypes.PDF
}

TEI_CONTENT = b'<tei>TEI TEI</tei>'

@pytest.fixture(name='grobid_service', autouse=True)
def _grobid_service():
  with patch.object(grobid_pipeline_module, 'grobid_service') as grobid_service:
    yield grobid_service

@pytest.fixture(name='grobid_service_instance')
def _grobid_service_instance(grobid_service):
  return grobid_service.return_value

@pytest.fixture(name='xslt_transformer_from_file', autouse=True)
def _xslt_transformer_from_file():
  with patch.object(grobid_pipeline_module, 'xslt_transformer_from_file') \
    as xslt_transformer_from_file:

    yield xslt_transformer_from_file

@pytest.fixture(name='xslt_transformer')
def _xslt_transformer(xslt_transformer_from_file):
  return xslt_transformer_from_file.return_value

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

class TestGrobidPipeline(object):
  def test_should_pass_grobid_url_and_action_to_grobid_service(self, config, args, grobid_service):
    args.grobid_url = 'http://grobid/api'
    args.grobid_action = '/action1'
    _run_pipeline(config, args, PDF_INPUT)
    grobid_service.assert_called_with(args.grobid_url, args.grobid_action, start_service=False)

  def test_should_auto_start_grobid_service_if_grobid_url_is_none(
    self, config, args, grobid_service):

    args.grobid_url = None
    args.grobid_action = '/action1'
    _run_pipeline(config, args, PDF_INPUT)
    grobid_service.assert_called_with(LOCAL_GROBID_API_URL, args.grobid_action, start_service=True)

  def test_should_pass_pdf_filename_and_content_to_grobid_service_instance(
    self, config, args, grobid_service_instance):

    _run_pipeline(config, args, PDF_INPUT)
    grobid_service_instance.assert_called_with(
      (PDF_INPUT['filename'], PDF_INPUT['content']),
      path=args.grobid_action
    )

  def test_should_use_process_header_if_includes_only_contains_header(
    self, config, args, grobid_service_instance):

    args.grobid_action = None
    _run_pipeline(config, args, extend_dict(PDF_INPUT, {
      StepDataProps.INCLUDES: {FieldNames.TITLE}
    }))
    grobid_service_instance.assert_called_with(
      (PDF_INPUT['filename'], PDF_INPUT['content']),
      path=GrobidApiPaths.PROCESS_HEADER_DOCUMENT
    )

  def test_should_use_process_full_text_if_includes_only_contains_references(
    self, config, args, grobid_service_instance):

    args.grobid_action = None
    _run_pipeline(config, args, extend_dict(PDF_INPUT, {
      StepDataProps.INCLUDES: {FieldNames.REFERENCES}
    }))
    grobid_service_instance.assert_called_with(
      (PDF_INPUT['filename'], PDF_INPUT['content']),
      path=GrobidApiPaths.PROCESS_FULL_TEXT_DOCUMENT
    )

  def test_should_return_tei_content_as_xml_content_without_xslt(
    self, config, args, grobid_service_instance):

    args.no_grobid_xslt = True
    grobid_service_instance.return_value = (PDF_INPUT['filename'], TEI_CONTENT)
    result = _run_pipeline(config, args, PDF_INPUT)
    assert result['content'] == TEI_CONTENT
    assert result['type'] == MimeTypes.TEI_XML

  def test_should_pass_xslt_path_to_xslt_transform_from_file(
    self, config, args, xslt_transformer_from_file):

    args.no_grobid_xslt = False
    args.no_grobid_pretty_print = False
    args.grobid_xslt_path = '/test.xsl'
    _run_pipeline(config, args, PDF_INPUT)
    xslt_transformer_from_file.assert_called_with(args.grobid_xslt_path, pretty_print=True)

  def test_should_return_apply_xslt_transform_to_tei_content(
    self, config, args, grobid_service_instance, xslt_transformer):

    args.no_grobid_xslt = False
    grobid_service_instance.return_value = (PDF_INPUT['filename'], TEI_CONTENT)
    result = _run_pipeline(config, args, PDF_INPUT)
    xslt_transformer.assert_called_with(TEI_CONTENT)
    assert result['content'] == xslt_transformer.return_value
    assert result['type'] == MimeTypes.JATS_XML

  def test_should_disable_pretty_print_xslt_output(
    self, config, args, xslt_transformer_from_file):

    args.no_grobid_xslt = False
    args.no_grobid_pretty_print = True
    args.grobid_xslt_path = '/test.xsl'
    _run_pipeline(config, args, PDF_INPUT)
    xslt_transformer_from_file.assert_called_with(args.grobid_xslt_path, pretty_print=False)
