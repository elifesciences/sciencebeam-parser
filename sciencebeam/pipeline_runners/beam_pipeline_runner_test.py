from mock import patch, MagicMock, DEFAULT, ANY

import pytest

import apache_beam as beam

from sciencebeam.utils.config import dict_to_config
from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam_gym.beam_utils.testing import (
  BeamTest,
  TestPipeline,
  get_counter_value
)

from . import beam_pipeline_runner as beam_pipeline_runner_module
from .beam_pipeline_runner import (
  configure_pipeline,
  parse_args,
  get_step_error_counter,
  get_step_ignored_counter,
  get_step_processed_counter
)


BASE_TEST_PATH = '.temp/test/conversion-pipeline'
BASE_DATA_PATH = BASE_TEST_PATH + '/data'
PDF_PATH = '*/*.pdf'
FILE_LIST_PATH = 'file-list.csv'
FILE_COLUMN = 'column1'

REL_PDF_FILE_WITHOUT_EXT_1 = '1/file'
PDF_FILE_1 = BASE_DATA_PATH + '/' + REL_PDF_FILE_WITHOUT_EXT_1 + '.pdf'

OUTPUT_PATH = BASE_TEST_PATH + '/out'
OUTPUT_SUFFIX = '.cv.xml'
OUTPUT_XML_FILE_1 = OUTPUT_PATH + '/' + REL_PDF_FILE_WITHOUT_EXT_1 + OUTPUT_SUFFIX

PDF_CONTENT_1 = b'pdf content 1'
XML_CONTENT_1 = b'<article>xml content 1</article>'
TEI_XML_CONTENT_1 = b'<TEI>tei content 1</TEI>'

MIN_ARGV = [
  '--data-path=' + BASE_DATA_PATH,
  '--source-path=' + PDF_PATH
]

@pytest.fixture(name='pipeline')
def _pipeline_mock():
  return MagicMock(name='pipeline')

@pytest.fixture(name='get_pipeline', autouse=True)
def _get_pipeline_mock(pipeline):
  with patch.object(beam_pipeline_runner_module, '_pipeline', pipeline):
    yield pipeline

@pytest.fixture(name='app_config')
def get_default_config():
  return dict_to_config({})

@pytest.fixture(name='args')
def get_default_args():
  app_config = get_default_config()
  opt = parse_args(MagicMock(), app_config, MIN_ARGV)
  opt.base_data_path = BASE_DATA_PATH
  opt.output_path = OUTPUT_PATH
  opt.output_suffix = OUTPUT_SUFFIX
  return opt

def get_file_path_args():
  opt = get_default_args()
  opt.source_path = PDF_PATH
  opt.source_file_list = None
  return opt

def get_file_list_args():
  opt = get_default_args()
  opt.source_path = None
  opt.source_file_list = BASE_DATA_PATH + '/file-list.tsv'
  opt.source_file_column = 'url'
  return opt

def patch_conversion_pipeline(**kwargs):
  always_mock = {
    'read_all_from_path',
    'ReadFileList',
    'FindFiles',
    'save_file_content'
  }

  return patch.multiple(
    beam_pipeline_runner_module,
    **{
      k: kwargs.get(k, DEFAULT)
      for k in always_mock
    }
  )

@pytest.mark.slow
class TestConfigurePipeline(BeamTest):
  def test_should_pass_pdf_pattern_to_find_files_and_read_pdf_file(self, pipeline, app_config):
    with patch_conversion_pipeline() as mocks:
      opt = get_file_path_args()
      with TestPipeline() as p:
        mocks['FindFiles'].return_value = beam.Create([PDF_FILE_1])
        configure_pipeline(p, opt, pipeline, app_config)

      mocks['FindFiles'].assert_called_with(
        BASE_DATA_PATH + '/' + PDF_PATH
      )
      mocks['read_all_from_path'].assert_called_with(
        PDF_FILE_1
      )

  def test_should_pass_pdf_file_list_and_limit_to_read_file_list_and_read_pdf_file(
    self, pipeline, app_config):

    with patch_conversion_pipeline() as mocks:
      opt = get_file_list_args()
      opt.limit = 100
      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([PDF_FILE_1])
        configure_pipeline(p, opt, pipeline, app_config)

      mocks['ReadFileList'].assert_called_with(
        opt.source_file_list, column=opt.source_file_column, limit=opt.limit
      )
      mocks['read_all_from_path'].assert_called_with(
        PDF_FILE_1
      )

  def test_should_pass_around_values_with_single_step(self, pipeline, app_config):
    with patch_conversion_pipeline() as mocks:
      opt = get_file_list_args()

      step1 = MagicMock(name='step1')
      step1.get_supported_types.return_value = {MimeTypes.PDF}
      step1.return_value = {
        'content': XML_CONTENT_1
      }

      pipeline.get_steps.return_value = [step1]

      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([PDF_FILE_1])
        mocks['read_all_from_path'].return_value = PDF_CONTENT_1
        configure_pipeline(p, opt, pipeline, app_config)
        assert get_counter_value(p.run(), get_step_processed_counter(step1)) == 1

      step1.assert_called_with({
        'content': PDF_CONTENT_1,
        'source_filename': PDF_FILE_1,
        'filename': PDF_FILE_1,
        'type': MimeTypes.PDF
      })
      mocks['save_file_content'].assert_called_with(
        OUTPUT_XML_FILE_1,
        XML_CONTENT_1
      )

  def test_should_pass_around_values_with_multiple_steps(self, pipeline, app_config):
    with patch_conversion_pipeline() as mocks:
      opt = get_file_list_args()

      step1 = MagicMock(name='step1')
      step1.get_supported_types.return_value = {MimeTypes.PDF}
      step1.return_value = {
        'content': TEI_XML_CONTENT_1,
        'type': MimeTypes.TEI_XML
      }

      step2 = MagicMock(name='step2')
      step2.get_supported_types.return_value = {MimeTypes.TEI_XML}
      step2.return_value = {
        'content': XML_CONTENT_1,
        'type': MimeTypes.JATS_XML
      }

      pipeline.get_steps.return_value = [step1, step2]

      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([PDF_FILE_1])
        mocks['read_all_from_path'].return_value = PDF_CONTENT_1
        configure_pipeline(p, opt, pipeline, app_config)

      step2.assert_called_with({
        'content': TEI_XML_CONTENT_1,
        'source_filename': PDF_FILE_1,
        'filename': PDF_FILE_1,
        'type': MimeTypes.TEI_XML
      })
      mocks['save_file_content'].assert_called_with(
        OUTPUT_XML_FILE_1,
        XML_CONTENT_1
      )

  def test_should_skip_item_causing_exception_and_increase_error_count(self, pipeline, app_config):
    with patch_conversion_pipeline() as mocks:
      opt = get_file_list_args()

      step1 = MagicMock(name='step1')
      step1.get_supported_types.return_value = {MimeTypes.PDF}
      step1.side_effect = RuntimeError('doh1')

      pipeline.get_steps.return_value = [step1]

      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([PDF_FILE_1])
        mocks['read_all_from_path'].return_value = PDF_CONTENT_1
        configure_pipeline(p, opt, pipeline, app_config)
        assert get_counter_value(p.run(), get_step_error_counter(step1)) == 1

      mocks['save_file_content'].assert_not_called()

  def test_should_skip_step_if_data_type_doesnt_match_and_increase_ignored_count(
    self, pipeline, app_config):

    with patch_conversion_pipeline() as mocks:
      opt = get_file_list_args()

      step1 = MagicMock(name='step1')
      step1.get_supported_types.return_value = {'other'}

      pipeline.get_steps.return_value = [step1]

      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([PDF_FILE_1])
        mocks['read_all_from_path'].return_value = PDF_CONTENT_1
        configure_pipeline(p, opt, pipeline, app_config)
        assert get_counter_value(p.run(), get_step_ignored_counter(step1)) == 1

class TestParseArgs(object):
  def test_should_parse_minimum_number_of_arguments(self, pipeline):
    parse_args(pipeline, get_default_config(), MIN_ARGV)

  def test_should_raise_error_if_no_source_argument_was_provided(self, pipeline):
    with pytest.raises(SystemExit):
      parse_args(pipeline, get_default_config(), [
        '--data-path=' + BASE_DATA_PATH
      ])

  def test_should_allow_source_path_to_be_specified(self, pipeline):
    args = parse_args(pipeline, get_default_config(), [
      '--data-path=' + BASE_DATA_PATH,
      '--source-path=' + PDF_PATH
    ])
    assert args.source_path == PDF_PATH

  def test_should_allow_source_file_list_and_column_to_be_specified(self, pipeline):
    args = parse_args(pipeline, get_default_config(), [
      '--data-path=' + BASE_DATA_PATH,
      '--source-file-list=' + FILE_LIST_PATH,
      '--source-file-column=' + FILE_COLUMN
    ])
    assert args.source_file_list == FILE_LIST_PATH
    assert args.source_file_column == FILE_COLUMN

  def test_should_call_pipeline_add_arguments(self, pipeline):
    app_config = get_default_config()
    parse_args(pipeline, app_config, MIN_ARGV)
    pipeline.add_arguments.assert_called_with(ANY, app_config, MIN_ARGV)
