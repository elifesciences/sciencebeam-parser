import logging
from mock import patch, MagicMock

import pytest

from sciencebeam.utils.config import dict_to_config

from . import simple_pipeline as simple_pipeline_module
from .simple_pipeline import create_simple_pipeline_from_config

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
  with patch.object(simple_pipeline_module, 'import_module') as import_module:
    yield import_module

@pytest.fixture(name='pipeline_module')
def _pipeline_module(import_module):
  return import_module.return_value

def setup_module():
  logging.basicConfig(level='DEBUG')

class TestCreateSimlePipelineFromConfig(object):
  def test_should_call_import_module_with_configured_default_pipeline(self, import_module):
    config = dict_to_config(DEFAULT_CONFIG)
    create_simple_pipeline_from_config(config)
    import_module.assert_called_with(DEFAULT_PIPELINE_MODULE)

  def test_should_load_steps_and_run_them_on_convert(self, pipeline_module):
    config = dict_to_config(DEFAULT_CONFIG)
    step = MagicMock(name='step')
    pipeline_module.get_pipeline_steps.return_value = [step]
    pipeline = create_simple_pipeline_from_config(config)
    assert (
      pipeline.convert(pdf_content=PDF_CONTENT, pdf_filename=PDF_FILENAME) ==
      step.return_value
    )
