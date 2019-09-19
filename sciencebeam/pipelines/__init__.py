import argparse
import logging
from abc import ABC, abstractmethod
from importlib import import_module
from configparser import ConfigParser  # pylint: disable=unused-import

from six import text_type

import requests
from requests import Session

from sciencebeam.utils.config import parse_list


LOGGER = logging.getLogger(__name__)


class FieldNames:
    TITLE = 'title'
    ABSTRACT = 'abstract'
    AUTHORS = 'authors'
    AFFILIATIONS = 'affiliations'
    REFERENCES = 'references'
    FULL_TEXT = 'full-text'


class StepDataProps:
    FILENAME = 'filename'
    CONTENT = 'content'
    INCLUDES = 'includes'
    TYPE = 'type'


class Pipeline(ABC):
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


class PipelineStep(ABC):
    @abstractmethod
    def get_supported_types(self):
        pass

    @abstractmethod
    def __call__(self, data, context: dict = None):
        pass


class RequestsPipelineStep(ABC):
    REQUESTS_SESSION_KEY = 'requests_session'

    def __init__(self, api_url: str):
        self._api_url = api_url

    def post_data(self, data: dict, session: requests.Session, **kwargs) -> requests.Response:
        LOGGER.debug('session: %s', session)
        response = session.post(
            self._api_url,
            headers={'Content-Type': data['type']},
            data=data['content'],
            **kwargs
        )
        response.raise_for_status()
        return response

    @abstractmethod
    def process_request(self, data: dict, session: Session, context: dict = None):
        pass

    def get_context_request_params_dict(self, context: dict) -> dict:
        LOGGER.debug('context: %s', context)
        request_args = (context or {}).get('request_args', {})
        LOGGER.debug('request_args: %s', request_args)
        try:
            return request_args.to_dict()
        except AttributeError:
            return dict(request_args)

    def get_data_request_params_dict(self, data: dict) -> dict:
        filename = (data or {}).get('filename')
        if filename:
            return {'filename': filename}
        return {}

    def get_default_params(self, data: dict, context: dict):
        return {
            **self.get_context_request_params_dict(context=context),
            **self.get_data_request_params_dict(data=data)
        }

    def __call__(self, data, context: dict = None):
        session = (context or {}).get(RequestsPipelineStep.REQUESTS_SESSION_KEY)
        if session is None:
            with requests.Session() as session:
                LOGGER.debug('no session provided, creating new session: %s', session)
                return self.process_request(data, session, context=context)
        return self.process_request(data, session, context=context)

    def __str__(self):
        return type(self).__name__

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, str(self))


class FunctionPipelineStep(PipelineStep):
    def __init__(self, fn, supported_types, name):
        self.fn = fn
        self.supported_types = supported_types
        self.name = name

    def get_supported_types(self):
        return self.supported_types

    def __call__(self, data, context: dict = None):
        return self.fn(data, context=context)

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
    pipelines = [
        pipeline_module.PIPELINE for pipeline_module in pipeline_modules
    ]
    if len(pipelines) == 1:
        return pipelines[0]
    return ChainedPipeline(pipelines)


def get_pipeline_expression_for_configuration(config, name=None):
    # type: (ConfigParser) -> str
    pipelines = config[u'pipelines']
    pipeline_names = parse_list(name or u'default')
    expressions = [pipelines[pipeline_name] for pipeline_name in pipeline_names]
    return text_type(', ').join(
        pipelines.get(expression, expression)
        for expression in expressions
    )


def get_pipeline_for_configuration(config, name=None):
    # type: (ConfigParser) -> Pipeline
    return get_pipeline_for_pipeline_expression(
        get_pipeline_expression_for_configuration(config, name=name)
    )


def add_pipeline_args(parser):
    pipeline_group = parser.add_argument_group('pipeline')
    pipeline_group.add_argument(
        '--pipeline', required=False,
        help='Pipeline to use'
    )


def parse_pipeline_args(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    add_pipeline_args(parser)
    args, _ = parser.parse_known_args(argv)
    return args


def get_pipeline_for_configuration_and_args(config, args=None, argv=None):
    args = parse_pipeline_args(argv) if args is None else args
    pipeline_name = args.pipeline
    return get_pipeline_for_configuration(config, name=pipeline_name)
