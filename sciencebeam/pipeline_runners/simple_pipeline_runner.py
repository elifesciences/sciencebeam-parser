from importlib import import_module

import logging

LOGGER = logging.getLogger(__name__)

class SimplePipelineRunner(object):
  def __init__(self, steps):
    LOGGER.debug('creating pipeline with steps: %s', steps)
    self._steps = steps

  def convert(self, pdf_content, pdf_filename):
    # type: (str, str) -> dict
    current_item = {
      'pdf_content': pdf_content,
      'pdf_filename': pdf_filename
    }
    for step in self._steps:
      LOGGER.debug('executing step: %s', step)
      current_item = step(current_item)
    return current_item

def create_simple_pipeline_runner_from_pipeline(pipeline, config, args):
  return SimplePipelineRunner(pipeline.get_steps(config, args))

def _pipeline(config):
  # type: (dict) -> Pipeline
  pipeline_module_name = config.get(u'pipelines', u'default')
  pipeline_module = import_module(pipeline_module_name)
  return pipeline_module.PIPELINE

def add_arguments(parser, config, argv=None):
  pipeline = _pipeline(config)
  pipeline.add_arguments(parser, config, argv=argv)

def create_simple_pipeline_runner_from_config(config, args):
  pipeline = _pipeline(config)
  return create_simple_pipeline_runner_from_pipeline(pipeline, config, args)
