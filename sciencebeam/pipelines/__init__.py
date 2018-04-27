from abc import ABCMeta, abstractmethod

from six import with_metaclass

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
