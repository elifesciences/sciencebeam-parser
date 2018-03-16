import logging
from mock import patch, MagicMock

import pytest

from sciencebeam.utils.config import dict_to_config

from . import simple_pipeline_runner as simple_pipeline_runner_module
from .simple_pipeline_runner import create_simple_pipeline_runner_from_config

DEFAULT_PIPELINE_MODULE = 'sciencebeam.pipelines.default_pipeline'

DEFAULT_CONFIG = {
  u'pipelines': {
    u'default': DEFAULT_PIPELINE_MODULE
  }
}

PDF_FILENAME = 'test.pdf'
PDF_CONTENT = b'pdf content'

@pytest.fixture(name='import_module', autouse=True)
def _import_module():
  with patch.object(simple_pipeline_runner_module, 'import_module') as import_module:
    yield import_module

@pytest.fixture(name='pipeline')
def _pipeline(import_module):
  return import_module.return_value.PIPELINE

@pytest.fixture(name='args')
def _args():
  return MagicMock(name='args')

@pytest.fixture(name='step')
def _step():
  return MagicMock(name='step')

def setup_module():
  logging.basicConfig(level='DEBUG')

class TestCreateSimlePipelineFromConfig(object):
  def test_should_call_import_module_with_configured_default_pipeline(self, import_module, args):
    config = dict_to_config(DEFAULT_CONFIG)
    create_simple_pipeline_runner_from_config(config, args)
    import_module.assert_called_with(DEFAULT_PIPELINE_MODULE)

  def test_should_pass_args_and_config_to_get_steps(self, pipeline, args, step):
    config = dict_to_config(DEFAULT_CONFIG)
    pipeline.get_steps.return_value = [step]
    create_simple_pipeline_runner_from_config(config, args)
    pipeline.get_steps.assert_called_with(config, args)

  def test_should_load_steps_and_run_them_on_convert(self, pipeline, args, step):
    config = dict_to_config(DEFAULT_CONFIG)
    pipeline.get_steps.return_value = [step]
    pipeline_runner = create_simple_pipeline_runner_from_config(config, args)
    assert (
      pipeline_runner.convert(pdf_content=PDF_CONTENT, pdf_filename=PDF_FILENAME) ==
      step.return_value
    )
