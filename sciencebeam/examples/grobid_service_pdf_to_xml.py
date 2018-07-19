from __future__ import absolute_import

import argparse
import os
from os.path import splitext
import subprocess
import errno
import logging

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions

from sciencebeam.beam_utils.fileio import ReadFileNamesAndContent, WriteToFile
from sciencebeam.beam_utils.core import MapKeys, MapValues
from sciencebeam.transformers.grobid_service import (
  grobid_service,
  GrobidApiPaths
)
from sciencebeam.transformers.xslt import xslt_transformer_from_file

def get_logger():
  return logging.getLogger(__name__)

def create_fn_api_runner():
  from apache_beam.runners.portability.fn_api_runner import FnApiRunner
  return FnApiRunner()

def configure_pipeline(p, opt):
  # read the files and create a collection with filename, content tuples
  pcoll = p | ReadFileNamesAndContent(opt.input)

  # map the pdf content to xml using Grobid
  # (grobid_service either accepts the content or tuples)
  output = pcoll | beam.Map(grobid_service(
    opt.grobid_url, opt.grobid_action, start_service=opt.start_grobid_service
  ))

  if opt.xslt_path:
    output |= MapValues(xslt_transformer_from_file(opt.xslt_path))

  # change the key (filename) from pdf to xml to reflect the new content
  output |= MapKeys(lambda k: '%s/%s' % (opt.output_path, splitext(k)[0].split('/')[-1] + opt.output_suffix))

  # write the files, using the key as the filename
  output |= WriteToFile()

def get_cloud_project():
  cmd = [
    'gcloud', '-q', 'config', 'list', 'project',
    '--format=value(core.project)'
  ]
  with open(os.devnull, 'w') as dev_null:
    try:
      res = subprocess.check_output(cmd, stderr=dev_null).strip()
      if not res:
        raise Exception(
          '--cloud specified but no Google Cloud Platform '
          'project found.\n'
          'Please specify your project name with the --project '
          'flag or set a default project: '
          'gcloud config set project YOUR_PROJECT_NAME'
        )
      return res
    except OSError as e:
      if e.errno == errno.ENOENT:
        raise Exception(
          'gcloud is not installed. The Google Cloud SDK is '
          'necessary to communicate with the Cloud ML service. '
          'Please install and set up gcloud.'
        )
      raise

def parse_args(argv=None):
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--input',
    required=True,
    help='Input file pattern to process.'
  )
  parser.add_argument(
    '--output_path',
    required=False,
    help='Output directory to write results to.'
  )
  parser.add_argument(
    '--output-suffix',
    required=False,
    default='.tei-header.xml',
    help='Output file suffix to add to the filename (excluding the file extension).')
  parser.add_argument(
    '--grobid-url',
    required=False,
    default=None,
    help='Base URL to the Grobid service')
  parser.add_argument(
    '--grobid-action',
    required=False,
    default=GrobidApiPaths.PROCESS_HEADER_DOCUMENT,
    help='Name of the Grobid action')
  parser.add_argument(
    '--xslt-path',
    required=False,
    help='XSLT template to apply')
  parser.add_argument(
    '--runner',
    required=False,
    default=None,
    help='Runner.')
  parser.add_argument(
    '--cloud',
    default=False,
    action='store_true'
  )
  parser.add_argument(
    '--project',
    type=str,
    help='The cloud project name to be used for running this pipeline'
  )
  parser.add_argument(
    '--num_workers',
    default=10,
    type=int,
    help='The number of workers.'
  )
  # parsed_args, other_args = parser.parse_known_args(argv)
  parsed_args = parser.parse_args(argv)

  if not parsed_args.grobid_url:
    parsed_args.grobid_url = 'http://localhost:8080/api'
    parsed_args.start_grobid_service = True
  else:
    parsed_args.start_grobid_service = False

  if not parsed_args.output_path:
    parsed_args.output_path = os.path.dirname(parsed_args.input.replace('/*/', '/'))
  if parsed_args.num_workers:
    parsed_args.autoscaling_algorithm = 'NONE'
    parsed_args.max_num_workers = parsed_args.num_workers
  parsed_args.setup_file = './setup.py'

  if parsed_args.cloud:
    # Flags which need to be set for cloud runs.
    default_values = {
      'project':
        get_cloud_project(),
      'temp_location':
        os.path.join(os.path.dirname(parsed_args.output_path), 'temp'),
      'runner':
        'DataflowRunner',
      'save_main_session':
        True,
    }
  else:
    # Flags which need to be set for local runs.
    default_values = {
      'runner': 'FnApiRunner',
    }

  get_logger().info('default_values: %s', default_values)
  for kk, vv in default_values.iteritems():
    if kk not in parsed_args or not vars(parsed_args)[kk]:
      vars(parsed_args)[kk] = vv
  get_logger().info('parsed_args: %s', parsed_args)

  return parsed_args


def run(argv=None):
  """Main entry point; defines and runs the tfidf pipeline."""
  known_args = parse_args(argv)

  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  pipeline_options = PipelineOptions.from_dictionary(vars(known_args))
  pipeline_options.view_as(SetupOptions).save_main_session = True

  runner = known_args.runner
  if runner == 'FnApiRunner':
    runner = create_fn_api_runner()

  with beam.Pipeline(runner, options=pipeline_options) as p:
    configure_pipeline(p, known_args)

    # Execute the pipeline and wait until it is completed.


if __name__ == '__main__':
  logging.basicConfig(level='INFO')

  run()
