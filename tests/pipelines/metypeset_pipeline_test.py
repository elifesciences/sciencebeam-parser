import argparse
from functools import reduce  # pylint: disable=W0622

from mock import patch, MagicMock

import pytest

from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam.pipelines import metypeset_pipeline as metypeset_pipeline_module
from sciencebeam.pipelines.metypeset_pipeline import PIPELINE

DOCX_INPUT = {
    'filename': 'test.docx',
    'content': b'DOCX insider 1',
    'type': MimeTypes.DOCX
}

XML_CONTENT = b'<XML>XML</XML>'


@pytest.fixture(name='requests_post', autouse=True)
def _requests_post(requests_session_post_mock: MagicMock):
    return requests_session_post_mock


@pytest.fixture(name='response')
def _response(requests_post):
    return requests_post.return_value


@pytest.fixture(name='MeTypesetApiStep')
def _metypeset_api_step():
    with patch.object(metypeset_pipeline_module, 'MeTypesetApiStep') \
            as cermine_api_step:

        yield cermine_api_step


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

        args.metypeset_url = 'http://metypeset/api'
        _run_pipeline(config, args, DOCX_INPUT)
        requests_post.assert_called_with(
            args.metypeset_url,
            data=DOCX_INPUT['content'],
            headers={'Content-Type': MimeTypes.DOCX}
        )

    def test_should_return_xml_response(
            self, config, args, response):

        args.no_science_parse_xslt = True

        response.text = XML_CONTENT
        response.headers = {'Content-Type': MimeTypes.XML}

        result = _run_pipeline(config, args, DOCX_INPUT)
        assert result['content'] == XML_CONTENT
        assert result['type'] == MimeTypes.XML
