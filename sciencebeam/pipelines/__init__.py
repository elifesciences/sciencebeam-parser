from abc import ABCMeta, abstractmethod
from importlib import import_module

from six import with_metaclass

from sciencebeam.utils.config import parse_list

class Pipeline(object, with_metaclass(ABCMeta)):
  @abstractmethod
  def add_arguments(self, parser, config, argv=None):
    pass

  @abstractmethod
  def get_steps(self, config, args):
    # type: (dict, object) -> list
    pass

class ChainedPipeline(Pipeline):
  def __init__(self, pipelines):
    self.pipelines = pipelines

  def add_arguments(self, parser, config, argv=None):
    for pipeline in self.pipelines:
      pipeline.add_arguments(parser, config, argv)

  def get_steps(self, config, args):
    return [
      step
      for pipeline in self.pipelines
      for step in pipeline.get_steps(config, args)
    ]

class PipelineStep(object, with_metaclass(ABCMeta)):
  @abstractmethod
  def get_supported_types(self):
    pass

  @abstractmethod
  def __call__(self, data):
    pass

class FunctionPipelineStep(PipelineStep):
  def __init__(self, fn, supported_types, name):
    self.fn = fn
    self.supported_types = supported_types
    self.name = name

  def get_supported_types(self):
    return self.supported_types

  def __call__(self, data):
    return self.fn(data)

  def __str__(self):
    return self.name

  def __repr__(self):
    return '%s(%s)' % (type(self).__name__, self.name)

def get_pipeline_for_pipeline_expression(pipeline_expression):
  # type: (str) -> Pipeline
  pipeline_module_names = parse_list(pipeline_expression)
  pipeline_modules = [
    import_module(pipeline_module_name)
    for pipeline_module_name in pipeline_module_names
  ]
  pipelines = [pipeline_module.PIPELINE for pipeline_module in pipeline_modules]
  if len(pipelines) == 1:
    return pipelines[0]
  return ChainedPipeline(pipelines)

def get_pipeline_expression_for_configuration(config, name=None):
  # type: (ConfigParser) -> str
  return config.get(u'pipelines', name or u'default')

def get_pipeline_for_configuration(config, name=None):
  # type: (ConfigParser) -> Pipeline
  return get_pipeline_for_pipeline_expression(
    get_pipeline_expression_for_configuration(config, name=name)
  )
