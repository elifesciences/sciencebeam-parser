from unittest.mock import patch, MagicMock

from six import text_type

import pytest

from sciencebeam.utils.config import dict_to_config
from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam import pipelines as pipelines_module
from sciencebeam.pipelines import (
    get_pipeline_expression_for_configuration,
    get_pipeline_for_configuration
)

DEFAULT_PIPELINE_MODULE = 'sciencebeam.pipelines.default_pipeline'
PIPELINE_MODULE_1 = 'sciencebeam.pipelines.pipeline1'
PIPELINE_MODULE_2 = 'sciencebeam.pipelines.pipeline2'

PIPELINE_1 = text_type('pipeline1')
PIPELINE_2 = text_type('pipeline2')

DEFAULT_CONFIG = {
    u'pipelines': {
        u'default': DEFAULT_PIPELINE_MODULE,
        PIPELINE_1: PIPELINE_MODULE_1,
        PIPELINE_2: PIPELINE_MODULE_2
    }
}


@pytest.fixture(name='import_module', autouse=True)
def _import_module():
    with patch.object(pipelines_module, 'import_module') as import_module:
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


class TestGetPipelineExpressionForConfiguration:
    def test_should_return_default_pipeline(self):
        config = dict_to_config(DEFAULT_CONFIG)
        assert get_pipeline_expression_for_configuration(config, '') == DEFAULT_PIPELINE_MODULE

    def test_should_return_specified_pipeline(self):
        config = dict_to_config(DEFAULT_CONFIG)
        assert get_pipeline_expression_for_configuration(config, PIPELINE_1) == PIPELINE_MODULE_1

    def test_should_return_concatenated_pipeline(self):
        config = dict_to_config(DEFAULT_CONFIG)
        assert get_pipeline_expression_for_configuration(
            config, '%s, %s' % (PIPELINE_1, PIPELINE_2)
        ) == '%s, %s' % (PIPELINE_MODULE_1, PIPELINE_MODULE_2)


class TestGetPipelineForConfiguration:
    def test_should_call_import_module_with_configured_default_pipeline(self, import_module):
        config = dict_to_config(DEFAULT_CONFIG)
        get_pipeline_for_configuration(config)
        import_module.assert_called_with(DEFAULT_PIPELINE_MODULE)

    def test_should_default_pipeline_to_point_to_another_pipeline_configuration(
            self, import_module):
        config = dict_to_config({
            u'pipelines': {
                u'default': u'custom',
                u'custom': DEFAULT_PIPELINE_MODULE
            }
        })
        get_pipeline_for_configuration(config)
        import_module.assert_called_with(DEFAULT_PIPELINE_MODULE)

    def test_should_pass_args_and_config_to_get_steps(self, pipeline, args, step):
        config = dict_to_config(DEFAULT_CONFIG)
        pipeline.get_steps.return_value = [step]
        get_pipeline_for_configuration(config).get_steps(config, args)
        pipeline.get_steps.assert_called_with(config, args)

    def test_should_return_pipeline_steps(self, pipeline, args, step):
        config = dict_to_config(DEFAULT_CONFIG)
        pipeline.get_steps.return_value = [step]
        pipeline = get_pipeline_for_configuration(config)
        step.get_supported_types.return_value = {MimeTypes.PDF}
        assert pipeline.get_steps(config, args) == [step]
