import logging
from mock import patch, DEFAULT

import pytest

import apache_beam as beam

from sciencebeam_gym.beam_utils.testing import (
  BeamTest,
  TestPipeline
)

import sciencebeam.examples.conversion_pipeline as conversion_pipeline
from sciencebeam.examples.conversion_pipeline import (
  configure_pipeline,
  parse_args,
  OutputExt
)


BASE_TEST_PATH = '.temp/test/conversion-pipeline'
BASE_DATA_PATH = BASE_TEST_PATH + '/data'
PDF_PATH = '*/*.pdf'
MODEL_EXPORT_DIR = BASE_TEST_PATH + '/model-export'
CV_MODEL_EXPORT_DIR = BASE_TEST_PATH + '/cv-model-export'
FILE_LIST_PATH = 'file-list.csv'
FILE_COLUMN = 'column1'

REL_PDF_FILE_WITHOUT_EXT_1 = '1/file'
PDF_FILE_1 = BASE_DATA_PATH + '/' + REL_PDF_FILE_WITHOUT_EXT_1 + '.pdf'
LXML_FILE_1 = BASE_DATA_PATH + '/' + REL_PDF_FILE_WITHOUT_EXT_1 + '.lxml'

OUTPUT_PATH = BASE_TEST_PATH + '/out'
OUTPUT_SUFFIX = '.cv.xml'
OUTPUT_XML_FILE_1 = OUTPUT_PATH + '/' + REL_PDF_FILE_WITHOUT_EXT_1 + OUTPUT_SUFFIX

PDF_CONTENT_1 = b'pdf content'
LXML_CONTENT_1 = b'<LXML>lxml content</LXML>'

fake_pdf_png_page = lambda i=0: 'fake pdf png page: %d' % i

MIN_ARGV = [
  '--data-path=' + BASE_DATA_PATH,
  '--pdf-path=' + PDF_PATH,
  '--crf-model=' + MODEL_EXPORT_DIR
]

def setup_module():
  logging.basicConfig(level='DEBUG')

def get_default_args():
  return parse_args(MIN_ARGV)

def patch_conversion_pipeline(**kwargs):
  always_mock = {
    'read_all_from_path',
    'load_structured_document',
    'convert_pdf_bytes_to_lxml',
    'convert_pdf_bytes_to_structured_document',
    'load_crf_model',
    'ReadFileList',
    'FindFiles',
    'predict_and_annotate_structured_document',
    'extract_annotated_structured_document_to_xml',
    'save_structured_document',
    'save_file_content',
    'GrobidXmlEnhancer',
    'pdf_bytes_to_png_pages',
    'InferenceModelWrapper',
    'annotate_structured_document_using_predicted_image_data'
  }

  return patch.multiple(
    conversion_pipeline,
    **{
      k: kwargs.get(k, DEFAULT)
      for k in always_mock
    }
  )

def _setup_mocks_for_pages(mocks, page_no_list, file_count=1):
  mocks['pdf_bytes_to_png_pages'].return_value = [
    fake_pdf_png_page(i) for i in page_no_list
  ]

@pytest.mark.slow
class TestConfigurePipeline(BeamTest):
  def test_should_pass_pdf_pattern_to_find_files_and_read_pdf_file(self):
    with patch_conversion_pipeline() as mocks:
      opt = get_default_args()
      opt.base_data_path = BASE_DATA_PATH
      opt.pdf_path = PDF_PATH
      opt.pdf_file_list = None
      with TestPipeline() as p:
        mocks['FindFiles'].return_value = beam.Create([PDF_FILE_1])
        configure_pipeline(p, opt)

      mocks['FindFiles'].assert_called_with(
        BASE_DATA_PATH + '/' + PDF_PATH
      )
      mocks['read_all_from_path'].assert_called_with(
        PDF_FILE_1
      )

  def test_should_pass_pdf_file_list_and_limit_to_read_file_list_and_read_pdf_file(self):
    with patch_conversion_pipeline() as mocks:
      opt = get_default_args()
      opt.base_data_path = BASE_DATA_PATH
      opt.pdf_path = None
      opt.pdf_file_list = BASE_DATA_PATH + '/file-list.tsv'
      opt.limit = 100
      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([PDF_FILE_1])
        configure_pipeline(p, opt)

      mocks['ReadFileList'].assert_called_with(
        opt.pdf_file_list, column='pdf_url', limit=opt.limit
      )
      mocks['read_all_from_path'].assert_called_with(
        PDF_FILE_1
      )

  def test_should_pass_around_values_with_default_pipeline(self):
    with patch_conversion_pipeline() as mocks:
      opt = get_default_args()
      opt.base_data_path = BASE_DATA_PATH
      opt.pdf_path = None
      opt.pdf_file_list = BASE_DATA_PATH + '/file-list.tsv'
      opt.output_path = OUTPUT_PATH
      opt.output_suffix = OUTPUT_SUFFIX
      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([PDF_FILE_1])
        mocks['read_all_from_path'].return_value = PDF_CONTENT_1
        configure_pipeline(p, opt)

      mocks['convert_pdf_bytes_to_structured_document'].assert_called_with(
        PDF_CONTENT_1, page_range=None, path=PDF_FILE_1
      )
      mocks['predict_and_annotate_structured_document'].assert_called_with(
        mocks['convert_pdf_bytes_to_structured_document'].return_value,
        mocks['load_crf_model'].return_value
      )
      mocks['extract_annotated_structured_document_to_xml'].assert_called_with(
        mocks['predict_and_annotate_structured_document'].return_value
      )
      mocks['save_file_content'].assert_called_with(
        OUTPUT_XML_FILE_1,
        mocks['extract_annotated_structured_document_to_xml'].return_value
      )

  def test_should_save_annotated_lxml_if_enabled(self):
    with patch_conversion_pipeline() as mocks:
      opt = get_default_args()
      opt.base_data_path = BASE_DATA_PATH
      opt.pdf_path = None
      opt.pdf_file_list = BASE_DATA_PATH + '/file-list.tsv'
      opt.output_path = OUTPUT_PATH
      opt.output_suffix = OUTPUT_SUFFIX
      opt.save_annot_lxml = True
      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([PDF_FILE_1])
        configure_pipeline(p, opt)

      mocks['save_structured_document'].assert_called_with(
        OUTPUT_PATH + '/' + REL_PDF_FILE_WITHOUT_EXT_1 + OutputExt.CRF_ANNOT_LXML,
        mocks['predict_and_annotate_structured_document'].return_value
      )

  def test_should_use_lxml_file_list_if_provided_and_load_structured_documents(self):
    with patch_conversion_pipeline() as mocks:
      opt = get_default_args()
      opt.base_data_path = BASE_DATA_PATH
      opt.pdf_path = None
      opt.pdf_file_list = None
      opt.lxml_file_list = BASE_DATA_PATH + '/file-list.tsv'
      opt.output_path = OUTPUT_PATH
      opt.output_suffix = OUTPUT_SUFFIX
      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([LXML_FILE_1])
        configure_pipeline(p, opt)

      mocks['extract_annotated_structured_document_to_xml'].assert_called_with(
        mocks['load_structured_document'].return_value
      )
      mocks['save_file_content'].assert_called_with(
        OUTPUT_XML_FILE_1,
        mocks['extract_annotated_structured_document_to_xml'].return_value
      )

  def test_should_use_crf_model_with_cv_model_if_enabled(self):
    with patch_conversion_pipeline() as mocks:
      inference_model_wrapper = mocks['InferenceModelWrapper'].return_value
      opt = get_default_args()
      opt.base_data_path = BASE_DATA_PATH
      opt.pdf_path = None
      opt.pdf_file_list = BASE_DATA_PATH + '/file-list.tsv'
      opt.output_path = OUTPUT_PATH
      opt.output_suffix = OUTPUT_SUFFIX
      opt.cv_model_export_dir = CV_MODEL_EXPORT_DIR
      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([PDF_FILE_1])
        mocks['read_all_from_path'].return_value = PDF_CONTENT_1
        _setup_mocks_for_pages(mocks, [1, 2])
        configure_pipeline(p, opt)

      mocks['convert_pdf_bytes_to_structured_document'].assert_called_with(
        PDF_CONTENT_1, page_range=None, path=PDF_FILE_1
      )

      # cv model
      inference_model_wrapper.assert_called_with(
        [fake_pdf_png_page(i) for i in [1, 2]]
      )
      mocks['annotate_structured_document_using_predicted_image_data'].assert_called_with(
        mocks['convert_pdf_bytes_to_structured_document'].return_value,
        inference_model_wrapper.return_value,
        inference_model_wrapper.get_color_map.return_value
      )

      # crf model should receive output from cv model
      mocks['predict_and_annotate_structured_document'].assert_called_with(
        mocks['annotate_structured_document_using_predicted_image_data'].return_value,
        mocks['load_crf_model'].return_value
      )
      mocks['extract_annotated_structured_document_to_xml'].assert_called_with(
        mocks['predict_and_annotate_structured_document'].return_value
      )

  def test_should_use_cv_model_only_if_enabled(self):
    with patch_conversion_pipeline() as mocks:
      inference_model_wrapper = mocks['InferenceModelWrapper'].return_value
      opt = get_default_args()
      opt.base_data_path = BASE_DATA_PATH
      opt.pdf_path = None
      opt.pdf_file_list = BASE_DATA_PATH + '/file-list.tsv'
      opt.output_path = OUTPUT_PATH
      opt.output_suffix = OUTPUT_SUFFIX
      opt.crf_model = None
      opt.cv_model_export_dir = CV_MODEL_EXPORT_DIR
      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([PDF_FILE_1])
        mocks['read_all_from_path'].return_value = PDF_CONTENT_1
        _setup_mocks_for_pages(mocks, [1, 2])
        configure_pipeline(p, opt)

      mocks['convert_pdf_bytes_to_structured_document'].assert_called_with(
        PDF_CONTENT_1, page_range=None, path=PDF_FILE_1
      )

      # cv model
      inference_model_wrapper.assert_called_with(
        [fake_pdf_png_page(i) for i in [1, 2]]
      )
      mocks['annotate_structured_document_using_predicted_image_data'].assert_called_with(
        mocks['convert_pdf_bytes_to_structured_document'].return_value,
        inference_model_wrapper.return_value,
        inference_model_wrapper.get_color_map.return_value
      )
      mocks['extract_annotated_structured_document_to_xml'].assert_called_with(
        mocks['annotate_structured_document_using_predicted_image_data'].return_value
      )

      # crf model not be called
      mocks['predict_and_annotate_structured_document'].assert_not_called()

  def test_should_use_grobid_if_enabled(self):
    with patch_conversion_pipeline() as mocks:
      grobid_xml_enhancer = mocks['GrobidXmlEnhancer'].return_value
      opt = get_default_args()
      opt.base_data_path = BASE_DATA_PATH
      opt.pdf_path = None
      opt.pdf_file_list = BASE_DATA_PATH + '/file-list.tsv'
      opt.output_path = OUTPUT_PATH
      opt.output_suffix = OUTPUT_SUFFIX
      opt.use_grobid = True
      opt.grobid_url = 'http://test/api'
      with TestPipeline() as p:
        mocks['ReadFileList'].return_value = beam.Create([PDF_FILE_1])
        mocks['read_all_from_path'].return_value = PDF_CONTENT_1
        mocks['convert_pdf_bytes_to_lxml'].return_value = LXML_CONTENT_1
        configure_pipeline(p, opt)

      mocks['GrobidXmlEnhancer'].assert_called_with(
        opt.grobid_url,
        start_service=opt.start_grobid_service
      )
      grobid_xml_enhancer.assert_called_with(
        mocks['extract_annotated_structured_document_to_xml'].return_value
      )
      mocks['save_file_content'].assert_called_with(
        OUTPUT_XML_FILE_1,
        grobid_xml_enhancer.return_value
      )

class TestParseArgs(object):
  def test_should_parse_minimum_number_of_arguments(self):
    parse_args(MIN_ARGV)

  def test_should_raise_error_if_no_source_argument_was_provided(self):
    with pytest.raises(SystemExit):
      parse_args([
        '--data-path=' + BASE_DATA_PATH,
        '--crf-model=' + MODEL_EXPORT_DIR
      ])

  def test_should_allow_pdf_path_to_be_specified(self):
    args = parse_args([
      '--data-path=' + BASE_DATA_PATH,
      '--pdf-path=' + PDF_PATH,
      '--crf-model=' + MODEL_EXPORT_DIR
    ])
    assert args.pdf_path == PDF_PATH

  def test_should_allow_pdf_file_list_and_column_to_be_specified(self):
    args = parse_args([
      '--data-path=' + BASE_DATA_PATH,
      '--pdf-file-list=' + FILE_LIST_PATH,
      '--pdf-file-column=' + FILE_COLUMN,
      '--crf-model=' + MODEL_EXPORT_DIR
    ])
    assert args.pdf_file_list == FILE_LIST_PATH
    assert args.pdf_file_column == FILE_COLUMN

  def test_should_allow_lxml_file_list_and_column_to_be_specified(self):
    args = parse_args([
      '--data-path=' + BASE_DATA_PATH,
      '--lxml-file-list=' + FILE_LIST_PATH,
      '--lxml-file-column=' + FILE_COLUMN
    ])
    assert args.lxml_file_list == FILE_LIST_PATH
    assert args.lxml_file_column == FILE_COLUMN

  def test_should_not_allow_crf_model_with_lxml_file_list(self):
    with pytest.raises(SystemExit):
      parse_args([
        '--data-path=' + BASE_DATA_PATH,
        '--lxml-file-list=' + FILE_LIST_PATH,
        '--lxml-file-column=' + FILE_COLUMN,
        '--crf-model=' + MODEL_EXPORT_DIR
      ])

  def test_should_not_allow_cv_model_with_lxml_file_list(self):
    with pytest.raises(SystemExit):
      parse_args([
        '--data-path=' + BASE_DATA_PATH,
        '--lxml-file-list=' + FILE_LIST_PATH,
        '--lxml-file-column=' + FILE_COLUMN,
        '--cv-model-export-dir=' + CV_MODEL_EXPORT_DIR
      ])

  def test_should_require_crf_or_cv_model_with_pdf_file_list(self):
    with pytest.raises(SystemExit):
      parse_args([
        '--data-path=' + BASE_DATA_PATH,
        '--pdf-file-list=' + FILE_LIST_PATH,
        '--pdf-file-column=' + FILE_COLUMN
      ])

  def test_should_require_crf_or_cv_model_with_pdf_path(self):
    with pytest.raises(SystemExit):
      parse_args([
        '--data-path=' + BASE_DATA_PATH,
        '--pdf-path=' + PDF_PATH
      ])

  def test_should_allow_crf_model_only_with_pdf_file_list(self):
    parse_args([
      '--data-path=' + BASE_DATA_PATH,
      '--pdf-file-list=' + FILE_LIST_PATH,
      '--pdf-file-column=' + FILE_COLUMN,
      '--crf-model=' + MODEL_EXPORT_DIR
    ])

  def test_should_allow_cv_model_only_with_pdf_file_list(self):
    parse_args([
      '--data-path=' + BASE_DATA_PATH,
      '--pdf-file-list=' + FILE_LIST_PATH,
      '--pdf-file-column=' + FILE_COLUMN,
      '--cv-model-export-dir=' + CV_MODEL_EXPORT_DIR
    ])

  def test_should_allow_crf_and_cv_model_only_with_pdf_file_list(self):
    parse_args([
      '--data-path=' + BASE_DATA_PATH,
      '--pdf-file-list=' + FILE_LIST_PATH,
      '--pdf-file-column=' + FILE_COLUMN,
      '--crf-model=' + MODEL_EXPORT_DIR,
      '--cv-model-export-dir=' + CV_MODEL_EXPORT_DIR
    ])
