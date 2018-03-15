from abc import ABCMeta, abstractmethod

from six import with_metaclass

class Pipeline(object, with_metaclass(ABCMeta)):
  @abstractmethod
  def add_arguments(self, parser, config, argv=None):
    pass

  @abstractmethod
  def get_steps(self, config, args):
    pass
