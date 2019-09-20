import argparse
from functools import reduce  # pylint: disable=W0622

from mock import patch, MagicMock

import pytest

from werkzeug.datastructures import MultiDict

from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam.pipelines import DEFAULT_REQUEST_TIMEOUT

from sciencebeam.pipelines import api_pipeline as api_pipeline_module
from sciencebeam.pipelines.api_pipeline import PIPELINE

PDF_INPUT = {
    'filename': 'test.pdf',
    'content': b'PDF insider 1',
    'type': MimeTypes.PDF
}

XML_CONTENT = b'<article>XML</article>'


@pytest.fixture(name='requests_post', autouse=True)
def _requests_post(requests_session_post_mock: MagicMock):
    return requests_session_post_mock


@pytest.fixture(name='response')
def _response(requests_post: MagicMock):
    return requests_post.return_value


@pytest.fixture(name='ApiStep')
def _api_step_class():
    with patch.object(api_pipeline_module, 'ApiStep') as ApiStep:
        yield ApiStep


@pytest.fixture(name='api_step')
def _api_step(ApiStep):
    yield ApiStep.return_value


@pytest.fixture(name='config')
def _config():
    return MagicMock(name='config')


@pytest.fixture(name='args')
def _args():
    return MagicMock(name='args')


def _run_pipeline(config, args, pdf_input, context: dict = None):
    parser = argparse.ArgumentParser()
    PIPELINE.add_arguments(parser, config)
    steps = PIPELINE.get_steps(config, args)
    return reduce(lambda value, step: step(value, context=context), steps, pdf_input)


class TestScienceParsePipeline:
    def test_should_pass_api_url_and_pdf_content_to_requests_post_call(
            self, config, args, requests_post):

        args.api_url = 'http://sciencebeam/api'
        _run_pipeline(config, args, PDF_INPUT)
        requests_post.assert_called_with(
            args.api_url,
            data=PDF_INPUT['content'],
            headers={'Content-Type': MimeTypes.PDF},
            params={'filename': PDF_INPUT['filename']},
            timeout=DEFAULT_REQUEST_TIMEOUT
        )

    def test_should_return_response_content(
            self, config, args, response):

        args.no_science_parse_xslt = True

        response.text = XML_CONTENT.decode('utf-8')
        response.content = XML_CONTENT
        response.headers = {'Content-Type': MimeTypes.JATS_XML}

        result = _run_pipeline(config, args, PDF_INPUT)
        assert result['content'] == XML_CONTENT
        assert result['type'] == MimeTypes.JATS_XML

    def test_should_pass_passed_in_url_parameters_to_requests_post_call(
            self, config, args, requests_post):

        args.api_url = 'http://sciencebeam/api'
        request_args = MultiDict([('remove_line_no', 'n')])
        _run_pipeline(config, args, PDF_INPUT, context={'request_args': request_args})
        requests_post.assert_called()
        actual_params = requests_post.call_args[1]['params']
        assert actual_params == {'filename': PDF_INPUT['filename'], 'remove_line_no': 'n'}
