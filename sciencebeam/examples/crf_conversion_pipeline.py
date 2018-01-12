from __future__ import absolute_import

import argparse
import os
import logging
import pickle
from itertools import islice
from io import BytesIO

import apache_beam as beam
from apache_beam.io.filesystems import FileSystems
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions

from lxml import etree

from sciencebeam_gym.utils.collection import (
  extend_dict,
  remove_keys_from_dict
)

from sciencebeam_gym.beam_utils.utils import (
  TransformAndCount,
  TransformAndLog,
  MapOrLog,
  PreventFusion
)

from sciencebeam_gym.beam_utils.csv import (
  ReadDictCsv
)

from sciencebeam_gym.beam_utils.io import (
  read_all_from_path,
  save_file_content
)

from sciencebeam_gym.beam_utils.main import (
  add_cloud_args,
  process_cloud_args,
  process_sciencebeam_gym_dep_args
)

from sciencebeam_gym.structured_document.lxml import (
  LxmlStructuredDocument
)

from sciencebeam_gym.beam_utils.io import (
  find_matching_filenames
)

from sciencebeam_gym.preprocess.preprocessing_utils import (
  join_if_relative_path,
  convert_pdf_bytes_to_lxml,
  parse_page_range,
  save_pages,
  pdf_bytes_to_png_pages
)

from sciencebeam_gym.inference_model.extract_to_xml import (
  extract_structured_document_to_xml
)

from sciencebeam_gym.models.text.crf.annotate_using_predictions import (
  predict_and_annotate_structured_document
)

from sciencebeam.transformers.grobid_xml_enhancer import (
  GrobidXmlEnhancer
)

from sciencebeam.examples.cv_conversion_pipeline import (
  InferenceModelWrapper,
  get_output_file,
  image_data_to_png,
  annotate_lxml_using_predicted_images
)

def get_logger():
  return logging.getLogger(__name__)

class MetricCounters(object):
  FILES = 'files'
  CONVERT_PDF_TO_LXML_ERROR = 'ConvertPdfToLxml_error_count'
  CONVERT_PDF_TO_PNG_ERROR = 'ConvertPdfToPng_error_count'
  CONVERT_LXML_TO_SVG_ANNOT_ERROR = 'ConvertPdfToSvgAnnot_error_count'
  CV_PREDICTION_ERROR = 'ComputerVisionPrediction_error_count'
  ANNOTATE_USING_PREDICTION_ERROR = 'AnnotateLxmlUsingPrediction_error_count'
  EXTRACT_TO_XML_ERROR = 'ExtractToXml_error_count'
  GROBID_ERROR = 'Grobid_error_count'

class OutputExt(object):
  CRF_ANNOT_LXML = '.crf.lxml.gz'
  CRF_CV_ANNOT_LXML = '.crf-cv.lxml.gz'
  CV_PNG = '.cv-png.zip'

def predict_and_annotate_lxml_content(lxml_content, model):
  structured_document = LxmlStructuredDocument(
    etree.parse(BytesIO(lxml_content))
  )
  predict_and_annotate_structured_document(structured_document, model)
  return etree.tostring(structured_document.root)

def extract_annotated_lxml_to_xml(annotated_lxml_content):
  structured_document = LxmlStructuredDocument(
    etree.parse(BytesIO(annotated_lxml_content))
  )

  xml_root = extract_structured_document_to_xml(structured_document)
  return etree.tostring(xml_root, pretty_print=True)

def load_crf_model(path):
  with FileSystems.open(path) as crf_model_f:
    return pickle.load(crf_model_f)

def configure_pipeline(p, opt):
  page_range = opt.pages

  cv_enabled = opt.cv_model_export_dir

  get_pipeline_output_file = lambda source_url, ext: get_output_file(
    source_url,
    opt.base_data_path,
    opt.output_path,
    ext
  )

  if opt.pdf_file_list:
    pdf_urls = (
      p |
      "ReadFileUrls" >> ReadDictCsv(opt.pdf_file_list, limit=opt.limit) |
      "TranslateFileUrls" >> beam.Map(lambda row: row['pdf_url'])
    )
  else:
    pdf_urls = (
      p |
      beam.Create([
        join_if_relative_path(opt.base_data_path, opt.pdf_path)
      ]) |
      "FindFiles" >> TransformAndLog(
        beam.FlatMap(
          lambda pattern: islice(
            find_matching_filenames(pattern),
            opt.limit
          )
        ),
        log_prefix='files: ',
        log_level='debug'
      )
    )

  lxml_content = (
    pdf_urls |
    PreventFusion() |

    "ReadFileContent" >> TransformAndCount(
      beam.Map(lambda pdf_url: {
        'pdf_filename': pdf_url,
        'pdf_content': read_all_from_path(pdf_url),
      }),
      MetricCounters.FILES
    ) |

    "ConvertPdfToLxml" >> MapOrLog(lambda v: extend_dict(v, {
      'lxml_content': convert_pdf_bytes_to_lxml(
        v['pdf_content'], path=v['pdf_filename'],
        page_range=page_range
      )
    }), log_fn=lambda e, v: (
      get_logger().warning(
        'caught exception (ignoring item): %s, pdf: %s',
        e, v['pdf_filename'], exc_info=e
      )
    ), error_count=MetricCounters.CONVERT_PDF_TO_LXML_ERROR)
  )

  if cv_enabled:
    image_size = (
      (opt.image_width, opt.image_height)
      if opt.image_width and opt.image_height
      else None
    )
    inference_model_wrapper = InferenceModelWrapper(opt.cv_model_export_dir)

    cv_predictions = (
      lxml_content |

      "ConvertPdfToPng" >> MapOrLog(lambda v: remove_keys_from_dict(
        extend_dict(v, {
          'pdf_png_pages':  list(pdf_bytes_to_png_pages(
            v['pdf_content'],
            dpi=90, # not used if the image is scaled
            image_size=image_size,
            page_range=page_range
          ))
        }),
        keys_to_remove={'pdf_content'}
      ), error_count=MetricCounters.CONVERT_PDF_TO_PNG_ERROR) |

      "ComputerVisionPrediction" >> MapOrLog(lambda v: remove_keys_from_dict(
        extend_dict(v, {
          'prediction_png_pages': inference_model_wrapper(v['pdf_png_pages']),
          'color_map': inference_model_wrapper.get_color_map()
        }),
        keys_to_remove={'pdf_png_pages'}
      ), error_count=MetricCounters.CV_PREDICTION_ERROR)
    )

    if opt.save_cv_output:
      _ = (
        cv_predictions |
        "SaveComputerVisionOutput" >> TransformAndLog(
          beam.Map(lambda v: save_pages(
            get_pipeline_output_file(
              v['pdf_filename'],
              OutputExt.CV_PNG
            ),
            '.png',
            [image_data_to_png(image_data) for image_data in v['prediction_png_pages']]
          )),
          log_fn=lambda x: get_logger().info('saved cv output: %s', x)
        )
      )

    cv_annotated_lxml = (
      cv_predictions |
      "AnnotateLxmlUsingCvPrediction" >> MapOrLog(lambda v: remove_keys_from_dict(
        extend_dict(v, {
          'lxml_content': annotate_lxml_using_predicted_images(
            v['lxml_content'], v['prediction_png_pages'], v['color_map']
          )
        }),
        keys_to_remove={'pdf_png_pages'}
      ), error_count=MetricCounters.ANNOTATE_USING_PREDICTION_ERROR)
    )

    lxml_content = cv_annotated_lxml

  model = load_crf_model(opt.crf_model)
  annotated_lxml = (
    lxml_content |
    "AnnotateLxmlUsingPrediction" >> MapOrLog(lambda v: remove_keys_from_dict(
      extend_dict(v, {
        'annotated_lxml_content': predict_and_annotate_lxml_content(
          v['lxml_content'], model
        )
      }),
      keys_to_remove={'lxml_content'}
    ), error_count=MetricCounters.ANNOTATE_USING_PREDICTION_ERROR)
  )

  if opt.save_annot_lxml:
    _ = (
      annotated_lxml |
      "SaveAnnotLxml" >> TransformAndLog(
        beam.Map(lambda v: save_file_content(
          get_pipeline_output_file(
            v['pdf_filename'],
            OutputExt.CRF_CV_ANNOT_LXML if cv_enabled else OutputExt.CRF_ANNOT_LXML
          ),
          v['annotated_lxml_content']
        )),
        log_fn=lambda x: get_logger().info('saved annoted lxml to: %s', x)
      )
    )

  extracted_xml = (
    annotated_lxml |
    "ExtractToXml" >> MapOrLog(lambda v: remove_keys_from_dict(
      extend_dict(v, {
        'extracted_xml': extract_annotated_lxml_to_xml(
          v['annotated_lxml_content']
        )
      }),
      keys_to_remove={'annotated_lxml_content'}
    ), error_count=MetricCounters.EXTRACT_TO_XML_ERROR)
  )

  if opt.use_grobid:
    enhancer = GrobidXmlEnhancer(
      opt.grobid_url, start_service=opt.start_grobid_service
    )
    extracted_xml = (
      extracted_xml |
      "GrobidEnhanceXml" >> MapOrLog(lambda v: extend_dict(v, {
        'extracted_xml': enhancer(
          v['extracted_xml']
        )
      }), error_count=MetricCounters.GROBID_ERROR)
    )

  _ = (
    extracted_xml |
    "WriteXml" >> TransformAndLog(
      beam.Map(lambda v: save_file_content(
        get_pipeline_output_file(
          v['pdf_filename'],
          opt.output_suffix
        ),
        v['extracted_xml']
      )),
      log_fn=lambda x: get_logger().info('saved xml to: %s', x)
    )
  )


def add_main_args(parser):
  parser.add_argument(
    '--data-path', type=str, required=True,
    help='base data path'
  )

  source_group = parser.add_mutually_exclusive_group(required=True)
  source_group.add_argument(
    '--pdf-path', type=str, required=False,
    help='path to pdf file(s), relative to data-path'
  )
  source_group.add_argument(
    '--pdf-file-list', type=str, required=False,
    help='path to pdf csv/tsv file list (with a "pdf_url" column; it may contain other columns)'
  )

  parser.add_argument(
    '--limit', type=int, required=False,
    help='limit the number of file pairs to process'
  )

  output_group = parser.add_argument_group('output')
  output_group.add_argument(
    '--output-path', required=False,
    help='Output directory to write results to.'
  )
  output_group.add_argument(
    '--output-suffix', required=False, default='.crf.xml',
    help='Output file suffix to add to the filename (excluding the file extension).'
  )

  parser.add_argument(
    '--save-annot-lxml', action='store_true', default=False,
    help='enable saving of annotated lxml'
  )

  grobid_group = parser.add_argument_group('Grobid')
  grobid_group.add_argument(
    '--use-grobid', action='store_true', default=False,
    help='enable the use of grobid'
  )
  grobid_group.add_argument(
    '--grobid-url', required=False, default=None,
    help='Base URL to the Grobid service'
  )

  parser.add_argument(
    '--debug', action='store_true', default=False,
    help='enable debug output'
  )

  parser.add_argument(
    '--pages', type=parse_page_range, default=None,
    help='only processes the selected pages'
  )

  crf_group = parser.add_argument_group('CRF')
  crf_group.add_argument(
    '--crf-model', type=str, required=True,
    help='path to saved crf model'
  )

  cv_group = parser.add_argument_group('CV')
  cv_group.add_argument(
    '--cv-model-export-dir', type=str, required=False,
    help='path to cv model export dir'
  )
  cv_group.add_argument(
    '--image-width', type=int, required=False,
    default=256,
    help='image width of resulting PNGs'
  )
  cv_group.add_argument(
    '--image-height', type=int, required=False,
    default=256,
    help='image height of resulting PNGs'
  )
  cv_group.add_argument(
    '--save-cv-output', action='store_true', default=False,
    help='enable saving of computer vision output (png pages)'
  )

def process_main_args(args):
  args.base_data_path = args.data_path.replace('/*/', '/')

  if not args.output_path:
    args.output_path = os.path.join(
      os.path.dirname(args.base_data_path),
      os.path.basename(args.base_data_path + '-results')
    )

  if args.use_grobid and not args.grobid_url:
    args.grobid_url = 'http://localhost:8080/api'
    args.start_grobid_service = True
  else:
    args.start_grobid_service = False

def parse_args(argv=None):
  parser = argparse.ArgumentParser()
  add_main_args(parser)
  add_cloud_args(parser)

  args = parser.parse_args(argv)

  if args.debug:
    logging.getLogger().setLevel('DEBUG')

  process_main_args(args)
  process_cloud_args(
    args, args.output_path,
    name='sciencebeam-convert'
  )
  process_sciencebeam_gym_dep_args(args)

  get_logger().info('args: %s', args)

  return args

def run(argv=None):
  args = parse_args(argv)

  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  pipeline_options = PipelineOptions.from_dictionary(vars(args))
  pipeline_options.view_as(SetupOptions).save_main_session = True

  with beam.Pipeline(args.runner, options=pipeline_options) as p:
    configure_pipeline(p, args)

    # Execute the pipeline and wait until it is completed.


if __name__ == '__main__':
  logging.basicConfig(level='INFO')

  run()
