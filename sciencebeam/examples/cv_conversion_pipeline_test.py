import logging
from mock import patch, DEFAULT

import pytest

import apache_beam as beam

from sciencebeam_gym.beam_utils.testing import (
  BeamTest,
  TestPipeline
)

import sciencebeam.examples.cv_conversion_pipeline as cv_conversion_pipeline
from sciencebeam.examples.cv_conversion_pipeline import (
  configure_pipeline,
  parse_args
)


BASE_TEST_PATH = '.temp/test/cv-conversion-pipeline'
BASE_DATA_PATH = BASE_TEST_PATH + '/data'
PDF_PATH = '*/*.pdf'
MODEL_EXPORT_DIR = BASE_TEST_PATH + '/model-export'

REL_PDF_FILE_WITHOUT_EXT_1 = '1/file'
PDF_FILE_1 = BASE_DATA_PATH + '/' + REL_PDF_FILE_WITHOUT_EXT_1 + '.pdf'

OUTPUT_PATH = BASE_TEST_PATH + '/out'
OUTPUT_SUFFIX = '.cv.xml'
OUTPUT_XML_FILE_1 = OUTPUT_PATH + '/' + REL_PDF_FILE_WITHOUT_EXT_1 + OUTPUT_SUFFIX

PDF_CONTENT_1 = b'pdf content'
LXML_CONTENT_1 = b'<LXML>lxml content</LXML>'

fake_pdf_png_page = lambda i=0: 'fake pdf png page: %d' % i

MIN_ARGV = [
  '--data-path=' + BASE_DATA_PATH,
  '--pdf-path=' + PDF_PATH,
  '--model-export-dir=' + MODEL_EXPORT_DIR
]

def setup_module():
  logging.basicConfig(level='DEBUG')

def get_default_args():
  return parse_args(MIN_ARGV)

def _setup_mocks_for_pages(mocks, page_no_list, file_count=1):
  mocks['pdf_bytes_to_png_pages'].return_value = [
    fake_pdf_png_page(i) for i in page_no_list
  ]

def patch_conversion_pipeline(**kwargs):
  always_mock = {
    'find_matching_filenames',
    'read_all_from_path',
    'pdf_bytes_to_png_pages',
    'convert_pdf_bytes_to_lxml',
    'save_pages',
    'ReadDictCsv',
    'create_inference_model_wrapper',
    'annotate_lxml_using_predicted_images',
    'extract_annotated_lxml_to_xml',
    'save_file_content',
    'parse_color_map_from_file',
    'GrobidXmlEnhancer'
  }

  return patch.multiple(
    cv_conversion_pipeline,
    **{
      k: kwargs.get(k, DEFAULT)
      for k in always_mock
    }
  )

@pytest.mark.slow
class TestConfigurePipeline(BeamTest):
  def test_should_pass_pdf_pattern_to_find_matching_filenames_and_read_pdf_file(self):
    with patch_conversion_pipeline() as mocks:
      opt = get_default_args()
      opt.base_data_path = BASE_DATA_PATH
      opt.pdf_path = PDF_PATH
      opt.pdf_file_list = None
      with TestPipeline() as p:
        mocks['find_matching_filenames'].return_value = [PDF_FILE_1]
        configure_pipeline(p, opt)

      mocks['find_matching_filenames'].assert_called_with(
        BASE_DATA_PATH + '/' + PDF_PATH
      )
      mocks['read_all_from_path'].assert_called_with(
        PDF_FILE_1
      )

  def test_should_pass_pdf_file_list_and_limit_to_read_dict_csv_and_read_pdf_file(self):
    with patch_conversion_pipeline() as mocks:
      opt = get_default_args()
      opt.base_data_path = BASE_DATA_PATH
      opt.pdf_path = None
      opt.pdf_file_list = BASE_DATA_PATH + '/file-list.tsv'
      opt.limit = 100
      with TestPipeline() as p:
        mocks['ReadDictCsv'].return_value = beam.Create([{
          'pdf_url': PDF_FILE_1
        }])
        configure_pipeline(p, opt)

      mocks['ReadDictCsv'].assert_called_with(
        opt.pdf_file_list, limit=opt.limit
      )
      mocks['read_all_from_path'].assert_called_with(
        PDF_FILE_1
      )

  def test_should_pass_around_values_with_default_pipeline(self):
    with patch_conversion_pipeline() as mocks:
      inference_model_wrapper = mocks['create_inference_model_wrapper'].return_value
      opt = get_default_args()
      opt.base_data_path = BASE_DATA_PATH
      opt.pdf_path = None
      opt.pdf_file_list = BASE_DATA_PATH + '/file-list.tsv'
      opt.output_path = OUTPUT_PATH
      opt.output_suffix = OUTPUT_SUFFIX
      with TestPipeline() as p:
        mocks['ReadDictCsv'].return_value = beam.Create([{
          'pdf_url': PDF_FILE_1
        }])
        mocks['read_all_from_path'].return_value = PDF_CONTENT_1
        mocks['convert_pdf_bytes_to_lxml'].return_value = LXML_CONTENT_1
        _setup_mocks_for_pages(mocks, [1, 2])
        configure_pipeline(p, opt)

      mocks['convert_pdf_bytes_to_lxml'].assert_called_with(
        PDF_CONTENT_1, page_range=None, path=PDF_FILE_1
      )
      inference_model_wrapper.assert_called_with(
        [fake_pdf_png_page(i) for i in [1, 2]]
      )
      mocks['annotate_lxml_using_predicted_images'].assert_called_with(
        LXML_CONTENT_1,
        inference_model_wrapper.return_value,
        mocks['parse_color_map_from_file'].return_value
      )
      mocks['extract_annotated_lxml_to_xml'].assert_called_with(
        mocks['annotate_lxml_using_predicted_images'].return_value
      )
      mocks['save_file_content'].assert_called_with(
        OUTPUT_XML_FILE_1,
        mocks['extract_annotated_lxml_to_xml'].return_value
      )

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
        mocks['ReadDictCsv'].return_value = beam.Create([{
          'pdf_url': PDF_FILE_1
        }])
        mocks['read_all_from_path'].return_value = PDF_CONTENT_1
        mocks['convert_pdf_bytes_to_lxml'].return_value = LXML_CONTENT_1
        _setup_mocks_for_pages(mocks, [1, 2])
        configure_pipeline(p, opt)

      mocks['GrobidXmlEnhancer'].assert_called_with(
        opt.grobid_url,
        start_service=opt.start_grobid_service
      )
      grobid_xml_enhancer.assert_called_with(
        mocks['extract_annotated_lxml_to_xml'].return_value
      )
      mocks['save_file_content'].assert_called_with(
        OUTPUT_XML_FILE_1,
        grobid_xml_enhancer.return_value
      )
