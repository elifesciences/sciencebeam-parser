import argparse
from functools import reduce  # pylint: disable=W0622

from unittest.mock import patch, MagicMock

import pytest

from lxml import etree
from lxml.builder import E

from sciencebeam_utils.utils.collection import extend_dict

from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam.pipelines import sciencebeam_autocut_pipeline as \
    sciencebeam_autocut_pipeline_module
from sciencebeam.pipelines.sciencebeam_autocut_pipeline import PIPELINE


# Note: disable "not-callable" to avoid "E is not callable (not-callable)"
# pylint: disable=not-callable


TITLE_1 = 'Title 1'
TITLE_2 = 'Title 2'

UNICODE_CONTENT_1 = 'Unicode \u1234'


TITLE_XPATH = 'front/article-meta/title-group/article-title'


def _generate_xml_with_title(title):
    return etree.tostring(
        E('article', E('front', E('article-meta', E('title-group', E('article-title', title)))))
    )


def _generate_content_with_title(title):
    return {
        'filename': 'test.xml',
        'content': _generate_xml_with_title(title),
        'type': MimeTypes.JATS_XML
    }


@pytest.fixture(name='requests_post', autouse=True)
def _requests_post(requests_session_post_mock: MagicMock):
    requests_session_post_mock.return_value.text = ''
    return requests_session_post_mock


@pytest.fixture(name='response')
def _response(requests_post):
    return requests_post.return_value


@pytest.fixture(name='ScienceBeamAutocutApiStep')
def _sciencebeam_utocut_api_step():
    with patch.object(sciencebeam_autocut_pipeline_module, 'ScienceBeamAutocutApiStep') as mock:
        yield mock


@pytest.fixture(name='api_step')
def _api_step(ScienceBeamAutocutApiStep):
    yield ScienceBeamAutocutApiStep.return_value


@pytest.fixture(name='config')
def _config():
    return MagicMock(name='config')


@pytest.fixture(name='args')
def _args():
    args = MagicMock(name='args')
    args.sciencebeam_autocut_url = 'http://sciencebeam-autocut/api'
    args.sciencebeam_autocut_xpath = TITLE_XPATH
    return args


def _run_pipeline(config, args, xml_input):
    parser = argparse.ArgumentParser()
    PIPELINE.add_arguments(parser, config)
    steps = PIPELINE.get_steps(config, args)
    return reduce(lambda value, step: step(value), steps, xml_input)


class TestScienceBeamAutocutPipeline:
    def test_should_pass_api_url_and_title_to_requests_post_call(
            self, config, args, requests_post):

        _run_pipeline(config, args, _generate_content_with_title(TITLE_1))
        requests_post.assert_called()
        assert requests_post.call_args[1]['data'] == TITLE_1.encode('utf-8')

    def test_should_utf8_encode_unicode_title_to_requests_post_call(
            self, config, args, requests_post):

        _run_pipeline(config, args, _generate_content_with_title(UNICODE_CONTENT_1))
        requests_post.assert_called()
        assert requests_post.call_args[1]['data'] == UNICODE_CONTENT_1.encode('utf-8')

    def test_should_return_xml_with_updated_title(
            self, config, args, response):

        response.text = TITLE_2

        result = _run_pipeline(config, args, _generate_content_with_title(TITLE_1))
        assert result['content'] == _generate_xml_with_title(TITLE_2)
        assert result['type'] == MimeTypes.JATS_XML

    def test_should_replace_title_containing_elements(
            self, config, args, response):

        response.text = TITLE_2

        result = _run_pipeline(config, args, _generate_content_with_title(
            E('b', TITLE_1)
        ))
        assert result['content'] == _generate_xml_with_title(TITLE_2)
        assert result['type'] == MimeTypes.JATS_XML

    def test_should_preserve_title_containing_elements_if_not_changed(
            self, config, args, response):

        response.text = TITLE_1

        title_with_elements = E('b', TITLE_1)
        result = _run_pipeline(config, args, _generate_content_with_title(
            title_with_elements
        ))
        assert result['content'] == _generate_xml_with_title(title_with_elements)
        assert result['type'] == MimeTypes.JATS_XML

    def test_should_preserve_other_input_props(self, config, args):
        result = _run_pipeline(config, args, extend_dict(
            _generate_content_with_title(TITLE_1),
            {'other': 'other1'}
        ))
        assert result['other'] == 'other1'
