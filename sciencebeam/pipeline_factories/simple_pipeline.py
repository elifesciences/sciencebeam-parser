from importlib import import_module

import logging

LOGGER = logging.getLogger(__name__)

class SimplePipeline(object):
  def __init__(self, steps):
    LOGGER.debug('creating pipeline with steps: %s', steps)
    self._steps = steps

  def convert(self, pdf_content, pdf_filename):
    current_item = {
      'pdf_content': pdf_content,
      'pdf_filename': pdf_filename
    }
    for step in self._steps:
      LOGGER.debug('executing step: %s', step)
      current_item = step(current_item)
    return current_item

def create_simple_factory_from_module(pipeline_module):
  return SimplePipeline(pipeline_module.get_pipeline_steps())

def create_simple_pipeline_from_config(config):
  pipeline_module_name = config.get(u'pipelines', u'default')
  pipeline_module = import_module(pipeline_module_name)
  return create_simple_factory_from_module(pipeline_module)
