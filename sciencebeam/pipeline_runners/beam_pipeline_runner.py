from __future__ import absolute_import

import argparse
import os
import logging
import mimetypes

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
from apache_beam.metrics.metric import Metrics

from sciencebeam_gym.utils.collection import (
  extend_dict
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

from sciencebeam_gym.preprocess.preprocessing_utils import (
  join_if_relative_path,
  get_output_file
)

from sciencebeam.config.app_config import get_app_config

from .simple_pipeline_runner import _pipeline

LOGGER = logging.getLogger(__name__)

def get_logger():
  return logging.getLogger(__name__)

class MetricCounters(object):
  FILES = 'files'

class DataProps(object):
  SOURCE_FILENAME = 'source_filename'
  FILENAME = 'filename'
  CONTENT = 'content'
  TYPE = 'type'

def FileUrlSource(opt):
  if opt.source_file_list:
    return ReadFileList(opt.source_file_list, column=opt.source_file_column, limit=opt.limit)
  else:
    return FindFiles(join_if_relative_path(opt.base_data_path, opt.source_path))

def ReadFileContent():
  return "ReadFileContent" >> TransformAndCount(
    beam.Map(lambda file_url: {
      DataProps.SOURCE_FILENAME: file_url,
      DataProps.FILENAME: file_url,
      DataProps.CONTENT: read_all_from_path(file_url)
    }),
    MetricCounters.FILES
  )

def get_step_error_counter(step):
  return 'error_%s' % step

def get_step_ignored_counter(step):
  return 'ignored_%s' % step

def get_step_processed_counter(step):
  return 'processed_%s' % step

def execute_or_skip_step(step):
  supported_types = step.get_supported_types()
  processed_counter = Metrics.counter('PipelineStep', get_step_processed_counter(step))
  ignored_counter = Metrics.counter('PipelineStep', get_step_ignored_counter(step))

  def wrapper(x):
    data_type = x['type']
    if data_type in supported_types:
      get_logger().debug('excuting step %s: %s (%s)', step, x.keys(), data_type)
      result = extend_dict(x, step(x))
      get_logger().debug('result of step %s: %s (%s)', step, result.keys(), result.get('type'))
      processed_counter.inc()
      return result
    else:
      get_logger().debug(
        'skipping step %s, %s not in supported types (%s)', step, data_type, supported_types
      )
      ignored_counter.inc()
      return x
  return wrapper

def get_step_transform(step):
  step_name = str(step)
  return step_name >> MapOrLog(
    execute_or_skip_step(step),
    log_fn=lambda e, v: (
      get_logger().warning(
        'caught exception (ignoring item): %s, source file: %s, step: %s',
        e, v[DataProps.SOURCE_FILENAME], step_name, exc_info=e
      )
    ), error_count=get_step_error_counter(step)
  )

def configure_pipeline(p, opt, pipeline, config):
  get_pipeline_output_file = lambda source_url, ext: get_output_file(
    source_url,
    opt.base_data_path,
    opt.output_path,
    ext
  )

  steps = pipeline.get_steps(config, opt)

  LOGGER.info('steps: %s', steps)

  input_data = (
    p |
    FileUrlSource(opt) |
    PreventFusion() |
    ReadFileContent() |
    "Determine Type" >> beam.Map(lambda d: extend_dict(d, {
      DataProps.TYPE: mimetypes.guess_type(d[DataProps.SOURCE_FILENAME])[0]
    }))
  )

  result = input_data

  for step in steps:
    LOGGER.debug('step: %s', step)
    result |= get_step_transform(step)

  _ = (
    result |
    beam.Map(lambda x: LOGGER.info('result: %s (%s)', x.keys(), x[DataProps.TYPE]))
  )

  _ = (
    result |
    "WriteOutput" >> TransformAndLog(
      beam.Map(lambda v: save_file_content(
        get_pipeline_output_file(
          v[DataProps.SOURCE_FILENAME],
          opt.output_suffix
        ),
        v[DataProps.CONTENT]
      )),
      log_fn=lambda x: get_logger().info('saved output to: %s', x)
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
    '--source-path', type=str, required=False,
    help='path to source file(s), relative to data-path'
  )
  source_one_of_group.add_argument(
    '--source-file-list', type=str, required=False,
    help='path to source csv/tsv file list'
  )
  source_group.add_argument(
    '--source-file-column', type=str, required=False, default='url',
    help='the column of the source file list to use'
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
    '--output-suffix', required=False, default='.xml',
    help='Output file suffix to add to the filename (excluding the file extension).'
  )

  parser.add_argument(
    '--debug', action='store_true', default=False,
    help='enable debug output'
  )

def process_main_args(args):
  args.base_data_path = args.data_path.replace('/*/', '/')

  if not args.output_path:
    args.output_path = os.path.join(
      os.path.dirname(args.base_data_path),
      os.path.basename(args.base_data_path + '-results')
    )

def parse_args(pipeline, config, argv=None):
  parser = argparse.ArgumentParser()
  add_main_args(parser)
  add_cloud_args(parser)
  pipeline.add_arguments(parser, config, argv)

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
  config = get_app_config()
  pipeline = _pipeline(config)

  args = parse_args(pipeline, config, argv)

  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  pipeline_options = PipelineOptions.from_dictionary(vars(args))
  pipeline_options.view_as(SetupOptions).save_main_session = True

  with beam.Pipeline(args.runner, options=pipeline_options) as p:
    configure_pipeline(p, args, pipeline, config)

    # Execute the pipeline and wait until it is completed.


if __name__ == '__main__':
  logging.basicConfig(level='INFO')

  run()
