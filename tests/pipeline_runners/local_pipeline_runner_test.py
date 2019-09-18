import logging
from pathlib import Path
from unittest.mock import MagicMock
from typing import List

import pytest

import flask

from sciencebeam_utils.utils.file_list import save_file_list

from sciencebeam.utils.mime_type_constants import MimeTypes
from sciencebeam.utils.misc import dict_to_args

from sciencebeam.pipeline_runners.local_pipeline_runner import (
    parse_args,
    main
)

from tests.utils.mock_server import MockServer


LOGGER = logging.getLogger(__name__)

PDF_CONTENT_1 = b'pdf content 1'
XML_CONTENT_1 = b'<article>xml content 1</article>'
XML_CONTENT_2 = b'<article>xml content 2</article>'


DEFAULT_ARGS = {
    'data-path': '/path/to/source',
    'source-file-list': 'file-list.tsv',
    'source-file-column': 'source_url',
    'output-path': '/path/to/output',
    'output-suffix': '.xml',
    'pipeline': 'pipeline1'
}


DEFAULT_CONFIG = {}


OUTPUT_SUFFIX = '.xml'

INPUT_FILE_1 = 'file1.pdf'
INPUT_FILE_LIST_1 = [INPUT_FILE_1]
OUTPUT_FILE_1 = 'file1.xml'
FILE_LIST_FILENAME_1 = 'file-list.tsv'


@pytest.fixture(name='pipeline_mock')
def _pipeline_mock():
    return MagicMock(name='pipeline')


class TestParseArgs:
    def test_should_parse_default_args(self, pipeline_mock: MagicMock):
        parse_args(
            pipeline=pipeline_mock, config=DEFAULT_CONFIG, argv=dict_to_args(DEFAULT_ARGS)
        )

    def test_should_parse_request_args(self, pipeline_mock: MagicMock):
        args = parse_args(
            pipeline=pipeline_mock,
            config=DEFAULT_CONFIG,
            argv=dict_to_args({
                **DEFAULT_ARGS,
                'request-args': 'remove_line_no=n&remove_redline=n'
            })
        )
        assert args.request_args.to_dict() == {
            'remove_line_no': 'n',
            'remove_redline': 'n'
        }


class ApiEndToEndTestHelper:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.source_path = temp_dir.joinpath('source')
        self.output_path = temp_dir.joinpath('output')
        self.source_path.mkdir(parents=True, exist_ok=True)
        self.source_file_list_filename = None


    def get_output_file(self, filename: str = OUTPUT_FILE_1) -> Path:
        return self.output_path.joinpath(filename)


    def write_source_file_bytes(
            self, filename: str = INPUT_FILE_1, data: bytes = PDF_CONTENT_1):
        self.source_path.joinpath(filename).write_bytes(data)


    def write_source_file_list(
            self,
            filename: str = 'file-list.tsv',
            file_list: List[str] = None,
            column: str = 'source_url'):
        if file_list is None:
            file_list = INPUT_FILE_LIST_1
        self.source_file_list_filename = filename
        save_file_list(
            str(self.source_path.joinpath(filename)),
            file_list=file_list, column=column
        )

    def write_default_source_files(self):
        self.write_source_file_bytes()
        self.write_source_file_list()

    def get_args(self, api_url: str, source_file_list: str = None):
        args = {
            'data-path': str(self.source_path),
            'source-file-column': 'source_url',
            'output-path': str(self.output_path),
            'output-suffix': OUTPUT_SUFFIX,
            'pipeline': 'api',
            'api-url': api_url
        }
        if not source_file_list:
            source_file_list = self.source_file_list_filename
        if source_file_list:
            args['source-file-list'] = source_file_list
        return args


@pytest.fixture(name='api_end_to_end_test_helper')
def _api_end_to_end_test_helper(temp_dir: Path):
    return ApiEndToEndTestHelper(temp_dir=temp_dir)


@pytest.mark.slow
class TestMainEndToEnd:
    def test_should_convert_single_file_using_file_list(
            self, mock_server: MockServer,
            api_end_to_end_test_helper: ApiEndToEndTestHelper):
        api_url = mock_server.add_response(
            '/api/convert', XML_CONTENT_1,
            mimetype=MimeTypes.JATS_XML,
            methods=('POST',)
        )
        LOGGER.debug('api_url: %s', api_url)
        api_end_to_end_test_helper.write_source_file_bytes()
        api_end_to_end_test_helper.write_source_file_list(
            filename=FILE_LIST_FILENAME_1,
            file_list=[INPUT_FILE_1],
            column='source_url'
        )
        output_file = api_end_to_end_test_helper.get_output_file()
        main(dict_to_args(api_end_to_end_test_helper.get_args(
            api_url=api_url,
            source_file_list=FILE_LIST_FILENAME_1
        )))
        assert output_file.read_bytes() == XML_CONTENT_1

    def test_should_convert_single_file_using_file_path(
            self, mock_server: MockServer,
            api_end_to_end_test_helper: ApiEndToEndTestHelper):
        api_url = mock_server.add_response(
            '/api/convert', XML_CONTENT_1,
            mimetype=MimeTypes.JATS_XML,
            methods=('POST',)
        )
        LOGGER.debug('api_url: %s', api_url)
        api_end_to_end_test_helper.write_source_file_bytes()
        output_file = api_end_to_end_test_helper.get_output_file()
        main(dict_to_args({
            **api_end_to_end_test_helper.get_args(
                api_url=api_url,
                source_file_list=None
            ),
            'source-path': '*.pdf'
        }))
        assert output_file.read_bytes() == XML_CONTENT_1

    def test_should_skip_existing_file(
            self, mock_server: MockServer,
            api_end_to_end_test_helper: ApiEndToEndTestHelper):
        api_url = mock_server.add_response(
            '/api/convert', XML_CONTENT_2,
            mimetype=MimeTypes.JATS_XML,
            methods=('POST',)
        )
        LOGGER.debug('api_url: %s', api_url)
        api_end_to_end_test_helper.write_default_source_files()
        api_end_to_end_test_helper.output_path.mkdir(parents=True, exist_ok=True)
        output_file = api_end_to_end_test_helper.get_output_file()
        output_file.write_bytes(XML_CONTENT_1)
        main(dict_to_args({
            **api_end_to_end_test_helper.get_args(api_url=api_url),
            'resume': True
        }))
        assert output_file.read_bytes() == XML_CONTENT_1


    def test_should_pass_request_args(
            self, mock_server: MockServer,
            api_end_to_end_test_helper: ApiEndToEndTestHelper):
        received_request_args = {}

        def _callback():
            received_request_args.update(flask.request.args.to_dict())
            return flask.Response(XML_CONTENT_1, mimetype=MimeTypes.JATS_XML)

        api_url = mock_server.add_callback_response(
            '/api/convert',
            _callback,
            methods=('POST',)
        )
        LOGGER.debug('api_url: %s', api_url)
        api_end_to_end_test_helper.write_default_source_files()
        api_end_to_end_test_helper.output_path.mkdir(parents=True, exist_ok=True)
        main(dict_to_args({
            **api_end_to_end_test_helper.get_args(api_url=api_url),
            'request-args': 'remove_line_no=n'
        }))
        assert received_request_args.get('remove_line_no') == 'n'

    def test_should_retry_convert_api_call(
            self, mock_server: MockServer,
            api_end_to_end_test_helper: ApiEndToEndTestHelper):
        callbacks = [
            lambda: flask.Response('error', status=500),
            lambda: flask.Response(XML_CONTENT_1, mimetype=MimeTypes.JATS_XML),
        ]
        api_url = mock_server.add_multiple_callbacks_response(
            '/api/convert', callbacks,
            methods=('POST',)
        )
        LOGGER.debug('api_url: %s', api_url)
        api_end_to_end_test_helper.write_default_source_files()
        output_file = api_end_to_end_test_helper.get_output_file()
        main(dict_to_args({
            **api_end_to_end_test_helper.get_args(api_url=api_url),
            'fail-on-error': True
        }))
        assert output_file.read_bytes() == XML_CONTENT_1
