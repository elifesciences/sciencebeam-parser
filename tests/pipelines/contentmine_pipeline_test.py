import argparse
from functools import reduce  # pylint: disable=W0622

from unittest.mock import patch, MagicMock

import pytest

from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam.pipelines import DEFAULT_REQUEST_TIMEOUT

from sciencebeam.pipelines import contentmine_pipeline as contentmine_pipeline_module
from sciencebeam.pipelines.contentmine_pipeline import PIPELINE

PDF_INPUT = {
    'filename': 'test.pdf',
    'content': b'PDF insider 1',
    'type': MimeTypes.PDF
}

XML_CONTENT = b'<XML>XML</XML>'


@pytest.fixture(name='requests_post', autouse=True)
def _requests_post(requests_session_post_mock: MagicMock):
    return requests_session_post_mock


@pytest.fixture(name='response')
def _response(requests_post):
    return requests_post.return_value


@pytest.fixture(name='ContentMineApiStep')
def _contentmine_api_step():
    with patch.object(contentmine_pipeline_module, 'ContentMineApiStep') \
            as contentmine_api_step:

        yield contentmine_api_step


@pytest.fixture(name='api_step')
def _api_step(CermineApiStep):
    yield CermineApiStep.return_value


@pytest.fixture(name='config')
def _config():
    return MagicMock(name='config')


@pytest.fixture(name='args')
def _args():
    return MagicMock(name='args')


def _run_pipeline(config, args, pdf_input):
    parser = argparse.ArgumentParser()
    PIPELINE.add_arguments(parser, config)
    steps = PIPELINE.get_steps(config, args)
    return reduce(lambda value, step: step(value), steps, pdf_input)


class TestCerminePipeline:
    def test_should_pass_api_url_and_pdf_content_to_requests_post_call(
            self, config, args, requests_post):

        args.contentmine_url = 'http://contentmine/api'
        _run_pipeline(config, args, PDF_INPUT)
        requests_post.assert_called_with(
            args.contentmine_url,
            data=PDF_INPUT['content'],
            headers={'Content-Type': MimeTypes.PDF},
            timeout=DEFAULT_REQUEST_TIMEOUT
        )

    def test_should_return_xml_response(
            self, config, args, response):

        args.no_science_parse_xslt = True

        response.text = XML_CONTENT
        response.headers = {'Content-Type': MimeTypes.XML}

        result = _run_pipeline(config, args, PDF_INPUT)
        assert result['content'] == XML_CONTENT
        assert result['type'] == MimeTypes.XML
