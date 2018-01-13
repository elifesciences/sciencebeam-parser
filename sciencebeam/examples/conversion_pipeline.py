from __future__ import absolute_import

import argparse
import os
import logging
import pickle
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

from sciencebeam_gym.beam_utils.files import (
  ReadFileList,
  FindFiles
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

from sciencebeam_gym.structured_document.structured_document_loader import (
  load_structured_document
)

from sciencebeam_gym.structured_document.lxml import (
  LxmlStructuredDocument
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

from sciencebeam_gym.inference_model.annotate_using_predictions import (
  annotate_structured_document_using_predicted_images,
  AnnotatedImage
)

from sciencebeam.transformers.grobid_xml_enhancer import (
  GrobidXmlEnhancer
)

from sciencebeam.examples.cv_conversion_pipeline import (
  InferenceModelWrapper,
  get_output_file,
  image_data_to_png
)

def get_logger():
  return logging.getLogger(__name__)

class MetricCounters(object):
  FILES = 'files'
  READ_LXML_ERROR = 'read_lxml_error_count'
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

class DataProps(object):
  SOURCE_FILENAME = 'source_filename'
  PDF_CONTENT = 'pdf_content'
  STRUCTURED_DOCUMENT = 'structured_document'
  PDF_PNG_PAGES = 'pdf_png_pages'
  CV_PREDICTION_PNG_PAGES = 'cv_prediction_png_pages'
  COLOR_MAP = 'color_map'
  EXTRACTED_XML = 'extracted_xml'

def convert_pdf_bytes_to_structured_document(pdf_content, path=None, page_range=None):
  return LxmlStructuredDocument(etree.parse(BytesIO(
    convert_pdf_bytes_to_lxml(pdf_content, path=path, page_range=page_range)
  )))

def annotate_structured_document_using_predicted_image_data(
  structured_document, prediction_images, color_map):

  return annotate_structured_document_using_predicted_images(
    structured_document, (
      AnnotatedImage(prediction_image, color_map)
      for prediction_image in prediction_images
    )
  )

def extract_annotated_structured_document_to_xml(structured_document):
  xml_root = extract_structured_document_to_xml(structured_document)
  return etree.tostring(xml_root, pretty_print=True)

def load_crf_model(path):
  with FileSystems.open(path) as crf_model_f:
    return pickle.load(crf_model_f)

def save_structured_document(filename, structured_document):
  # only support saving lxml for now
  assert isinstance(structured_document, LxmlStructuredDocument)
  save_file_content(filename, etree.tostring(structured_document.root, pretty_print=True))

def add_read_pdfs_to_annotated_lxml_pipeline_steps(p, opt, get_pipeline_output_file):
  page_range = opt.pages

  cv_enabled = opt.cv_model_export_dir

  if opt.pdf_file_list:
    pdf_urls = p | ReadFileList(opt.pdf_file_list, column=opt.pdf_file_column, limit=opt.limit)
  else:
    pdf_urls = p | FindFiles(join_if_relative_path(opt.base_data_path, opt.pdf_path))

  lxml_content = (
    pdf_urls |
    PreventFusion() |

    "ReadPdfContent" >> TransformAndCount(
      beam.Map(lambda pdf_url: {
        DataProps.SOURCE_FILENAME: pdf_url,
        DataProps.PDF_CONTENT: read_all_from_path(pdf_url)
      }),
      MetricCounters.FILES
    ) |

    "ConvertPdfToLxml" >> MapOrLog(lambda v: extend_dict(v, {
      DataProps.STRUCTURED_DOCUMENT: convert_pdf_bytes_to_structured_document(
        v[DataProps.PDF_CONTENT], path=v[DataProps.SOURCE_FILENAME],
        page_range=page_range
      )
    }), log_fn=lambda e, v: (
      get_logger().warning(
        'caught exception (ignoring item): %s, pdf: %s',
        e, v[DataProps.SOURCE_FILENAME], exc_info=e
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
          DataProps.PDF_PNG_PAGES:  list(pdf_bytes_to_png_pages(
            v[DataProps.PDF_CONTENT],
            dpi=90, # not used if the image is scaled
            image_size=image_size,
            page_range=page_range
          ))
        }),
        keys_to_remove={DataProps.PDF_CONTENT}
      ), error_count=MetricCounters.CONVERT_PDF_TO_PNG_ERROR) |

      "ComputerVisionPrediction" >> MapOrLog(lambda v: remove_keys_from_dict(
        extend_dict(v, {
          DataProps.CV_PREDICTION_PNG_PAGES: inference_model_wrapper(v[DataProps.PDF_PNG_PAGES]),
          DataProps.COLOR_MAP: inference_model_wrapper.get_color_map()
        }),
        keys_to_remove={DataProps.PDF_PNG_PAGES}
      ), error_count=MetricCounters.CV_PREDICTION_ERROR)
    )

    if opt.save_cv_output:
      _ = (
        cv_predictions |
        "SaveComputerVisionOutput" >> TransformAndLog(
          beam.Map(lambda v: save_pages(
            get_pipeline_output_file(
              v[DataProps.SOURCE_FILENAME],
              OutputExt.CV_PNG
            ),
            '.png',
            [image_data_to_png(image_data) for image_data in v[DataProps.CV_PREDICTION_PNG_PAGES]]
          )),
          log_fn=lambda x: get_logger().info('saved cv output: %s', x)
        )
      )

    cv_annotated_lxml = (
      cv_predictions |
      "AnnotateLxmlUsingCvPrediction" >> MapOrLog(lambda v: remove_keys_from_dict(
        extend_dict(v, {
          DataProps.STRUCTURED_DOCUMENT: annotate_structured_document_using_predicted_image_data(
            v[DataProps.STRUCTURED_DOCUMENT],
            v[DataProps.CV_PREDICTION_PNG_PAGES],
            v[DataProps.COLOR_MAP]
          )
        }),
        keys_to_remove={DataProps.PDF_PNG_PAGES}
      ), error_count=MetricCounters.ANNOTATE_USING_PREDICTION_ERROR)
    )

    lxml_content = cv_annotated_lxml

  model = load_crf_model(opt.crf_model)
  annotated_lxml = (
    lxml_content |
    "AnnotateLxmlUsingCrfPrediction" >> MapOrLog(lambda v: extend_dict(v, {
      DataProps.STRUCTURED_DOCUMENT: predict_and_annotate_structured_document(
        v[DataProps.STRUCTURED_DOCUMENT], model
      )
    }), error_count=MetricCounters.ANNOTATE_USING_PREDICTION_ERROR)
  )

  if opt.save_annot_lxml:
    _ = (
      annotated_lxml |
      "SaveAnnotLxml" >> TransformAndLog(
        beam.Map(lambda v: save_structured_document(
          get_pipeline_output_file(
            v[DataProps.SOURCE_FILENAME],
            OutputExt.CRF_CV_ANNOT_LXML if cv_enabled else OutputExt.CRF_ANNOT_LXML
          ),
          v[DataProps.STRUCTURED_DOCUMENT]
        )),
        log_fn=lambda x: get_logger().info('saved annoted lxml to: %s', x)
      )
    )
  return annotated_lxml

def configure_pipeline(p, opt):
  get_pipeline_output_file = lambda source_url, ext: get_output_file(
    source_url,
    opt.base_data_path,
    opt.output_path,
    ext
  )

  if opt.lxml_file_list:
    lxml_urls = p | ReadFileList(opt.lxml_file_list, column=opt.lxml_file_column, limit=opt.limit)

    annotated_lxml = (
      lxml_urls |
      PreventFusion() |

      "ReadLxmlContent" >> TransformAndCount(
        MapOrLog(lambda url: {
          DataProps.SOURCE_FILENAME: url,
          DataProps.STRUCTURED_DOCUMENT: load_structured_document(url)
        }, error_count=MetricCounters.READ_LXML_ERROR),
        MetricCounters.FILES
      )
    )
  else:
    annotated_lxml = add_read_pdfs_to_annotated_lxml_pipeline_steps(
      p, opt, get_pipeline_output_file
    )

  extracted_xml = (
    annotated_lxml |
    "ExtractToXml" >> MapOrLog(lambda v: remove_keys_from_dict(
      extend_dict(v, {
        DataProps.EXTRACTED_XML: extract_annotated_structured_document_to_xml(
          v[DataProps.STRUCTURED_DOCUMENT]
        )
      }),
      keys_to_remove={DataProps.STRUCTURED_DOCUMENT}
    ), error_count=MetricCounters.EXTRACT_TO_XML_ERROR)
  )

  if opt.use_grobid:
    enhancer = GrobidXmlEnhancer(
      opt.grobid_url, start_service=opt.start_grobid_service
    )
    extracted_xml = (
      extracted_xml |
      "GrobidEnhanceXml" >> MapOrLog(lambda v: extend_dict(v, {
        DataProps.EXTRACTED_XML: enhancer(
          v[DataProps.EXTRACTED_XML]
        )
      }), error_count=MetricCounters.GROBID_ERROR)
    )

  _ = (
    extracted_xml |
    "WriteXml" >> TransformAndLog(
      beam.Map(lambda v: save_file_content(
        get_pipeline_output_file(
          v[DataProps.SOURCE_FILENAME],
          opt.output_suffix
        ),
        v[DataProps.EXTRACTED_XML]
      )),
      log_fn=lambda x: get_logger().info('saved xml to: %s', x)
    )
  )


def add_main_args(parser):
  parser.add_argument(
    '--data-path', type=str, required=True,
    help='base data path'
  )

  source_group = parser.add_argument_group('source')
  source_one_of_group = source_group.add_mutually_exclusive_group(required=True)
  source_one_of_group.add_argument(
    '--pdf-path', type=str, required=False,
    help='path to pdf file(s), relative to data-path'
  )
  source_one_of_group.add_argument(
    '--pdf-file-list', type=str, required=False,
    help='path to pdf csv/tsv file list'
  )
  source_group.add_argument(
    '--pdf-file-column', type=str, required=False, default='pdf_url',
    help='the column of the pdf file list to use'
  )
  source_one_of_group.add_argument(
    '--lxml-file-list', type=str, required=False,
    help='path to annotated lxml or svg pages zip file list'
    '; (CRF and CV models are not supported in this mode)'
  )
  source_group.add_argument(
    '--lxml-file-column', type=str, required=False, default='url',
    help='the column of the lxml file list to use'
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
    '--crf-model', type=str, required=False,
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

def process_main_args(args, parser):
  args.base_data_path = args.data_path.replace('/*/', '/')

  if not args.output_path:
    args.output_path = os.path.join(
      os.path.dirname(args.base_data_path),
      os.path.basename(args.base_data_path + '-results')
    )

  if args.lxml_file_list:
    if args.crf_model:
      parser.error('--crf-model cannot be used in conjunction with --lxml-file-list')

    if args.cv_model_export_dir:
      parser.error('--crf-model-export-dir cannot be used in conjunction with --lxml-file-list')
  else:
    if not args.crf_model:
      parser.error('--crf-model required in conjunction with --pdf-file-list or --pdf-path')

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

  process_main_args(args, parser)
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
