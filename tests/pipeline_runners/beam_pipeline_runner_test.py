import logging
from pathlib import Path

from unittest.mock import patch, MagicMock, DEFAULT, ANY

import pytest

from sciencebeam_utils.beam_utils.testing import (
    BeamTest,
    TestPipeline,
    get_counter_value
)

from sciencebeam.utils.config import dict_to_config
from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam.pipeline_runners import beam_pipeline_runner as beam_pipeline_runner_module
from sciencebeam.pipeline_runners.beam_pipeline_runner import (
    configure_pipeline,
    parse_args,
    get_step_error_counter,
    get_step_ignored_counter,
    get_step_processed_counter,
    main
)

from tests.utils.mock_server import MockServer


LOGGER = logging.getLogger(__name__)


BASE_TEST_PATH = '/tmp/test/conversion-pipeline'
BASE_DATA_PATH = BASE_TEST_PATH + '/data'
PDF_PATH = '*/*.pdf'
FILE_LIST_PATH = 'file-list.csv'
FILE_COLUMN = 'column1'

REL_PDF_FILE_WITHOUT_EXT_1 = '1/file'
PDF_FILE_1 = BASE_DATA_PATH + '/' + REL_PDF_FILE_WITHOUT_EXT_1 + '.pdf'

OUTPUT_PATH = BASE_TEST_PATH + '/out'
OUTPUT_SUFFIX = '.cv.xml'
OUTPUT_XML_FILE_1 = (
    OUTPUT_PATH + '/' +
    REL_PDF_FILE_WITHOUT_EXT_1 + OUTPUT_SUFFIX
)

PDF_CONTENT_1 = b'pdf content 1'
XML_CONTENT_1 = b'<article>xml content 1</article>'
TEI_XML_CONTENT_1 = b'<TEI>tei content 1</TEI>'

UNICODE_CONTENT_1 = u'Unicode \u1234'

MIN_ARGV = [
    '--data-path=' + BASE_DATA_PATH,
    '--source-path=' + PDF_PATH
]


@pytest.fixture(name='pipeline')
def _pipeline_mock():
    return MagicMock(name='pipeline')


@pytest.fixture(name='get_pipeline', autouse=False)
def _get_pipeline_mock(pipeline):
    with patch.object(
            beam_pipeline_runner_module,
            'get_pipeline_for_configuration_and_args') as mock:  # noqa: E125
        mock.return_value = pipeline
        yield mock


@pytest.fixture(name='beam_pipeline_mock', autouse=True)
def _beam_pipeline_mock():
    with patch('apache_beam.Pipeline', TestPipeline) as mock:
        yield mock


@pytest.fixture(name='app_config')
def get_default_config():
    return dict_to_config({})


@pytest.fixture(name='args')
def get_default_args(app_config):
    opt = parse_args(MagicMock(), app_config, MIN_ARGV)
    opt.base_data_path = BASE_DATA_PATH
    opt.output_path = OUTPUT_PATH
    opt.output_suffix = OUTPUT_SUFFIX
    return opt


@pytest.fixture(name='file_path_args')
def get_file_path_args(args):
    opt = args
    opt.source_path = PDF_PATH
    opt.source_file_list = None
    return opt


@pytest.fixture(name='file_list_args')
def get_file_list_args(args):
    opt = args
    opt.source_path = None
    opt.source_file_list = BASE_DATA_PATH + '/file-list.tsv'
    opt.source_file_column = 'url'
    return opt


@pytest.fixture(name='mocks')
def patch_conversion_pipeline(**kwargs):
    always_mock = {
        'get_remaining_file_list_for_args',
        'read_all_from_path',
        'save_file_content'
    }

    with patch.multiple(
            beam_pipeline_runner_module,
            **{
                k: kwargs.get(k, DEFAULT)
                for k in always_mock
            }) as mocks:
        yield mocks


def _convert_step(name, supported_types, response=None):
    step = MagicMock(name=name)
    step.get_supported_types.return_value = supported_types
    if response:
        step.return_value = response
    return step


def _pdf_step(name='pdf_step', response=None):
    return _convert_step(name, {MimeTypes.PDF}, response=response)


def _tei_step(name='tei_step', response=None):
    return _convert_step(name, {MimeTypes.TEI_XML}, response=response)


def _add_test_args(parser, *_, **__):
    parser.add_argument('--test-arg', required=True)
    LOGGER.debug('added test arg to parser: %s', parser)


@pytest.mark.slow
@pytest.mark.usefixtures('mocks')
class TestConfigurePipeline(BeamTest):
    def test_should_pass_args_to_get_remaining_file_list_for_args(
            self, pipeline, app_config, file_path_args, mocks):

        opt = file_path_args
        with TestPipeline() as p:
            mocks['get_remaining_file_list_for_args'].return_value = [PDF_FILE_1]
            configure_pipeline(p, opt, pipeline, app_config)

        mocks['get_remaining_file_list_for_args'].assert_called_with(opt)
        mocks['read_all_from_path'].assert_called_with(
            PDF_FILE_1
        )

    def test_should_pass_around_values_with_single_step(
            self, pipeline, app_config, file_list_args, mocks):
        opt = file_list_args

        step1 = _pdf_step(response={
            'content': XML_CONTENT_1
        })

        pipeline.get_steps.return_value = [step1]

        with TestPipeline() as p:
            mocks['get_remaining_file_list_for_args'].return_value = [PDF_FILE_1]
            mocks['read_all_from_path'].return_value = PDF_CONTENT_1
            configure_pipeline(p, opt, pipeline, app_config)
            assert get_counter_value(
                p.run(), get_step_processed_counter(step1)
            ) == 1

        step1.assert_called_with({
            'content': PDF_CONTENT_1,
            'source_filename': PDF_FILE_1,
            'filename': PDF_FILE_1,
            'type': MimeTypes.PDF
        })
        mocks['save_file_content'].assert_called_with(
            OUTPUT_XML_FILE_1,
            XML_CONTENT_1
        )

    def test_should_encode_string_when_saving(
            self, pipeline, app_config, file_list_args, mocks):
        opt = file_list_args

        step1 = _pdf_step(response={
            'content': UNICODE_CONTENT_1
        })

        pipeline.get_steps.return_value = [step1]

        with TestPipeline() as p:
            mocks['get_remaining_file_list_for_args'].return_value = [PDF_FILE_1]
            mocks['read_all_from_path'].return_value = PDF_CONTENT_1
            configure_pipeline(p, opt, pipeline, app_config)

        mocks['save_file_content'].assert_called_with(
            OUTPUT_XML_FILE_1,
            UNICODE_CONTENT_1.encode('utf-8')
        )

    def test_should_pass_around_values_with_multiple_steps(
            self, pipeline, app_config, file_list_args, mocks):
        opt = file_list_args

        step1 = _pdf_step(response={
            'content': TEI_XML_CONTENT_1,
            'type': MimeTypes.TEI_XML
        })

        step2 = _tei_step(response={
            'content': XML_CONTENT_1,
            'type': MimeTypes.JATS_XML
        })

        pipeline.get_steps.return_value = [step1, step2]

        with TestPipeline() as p:
            mocks['get_remaining_file_list_for_args'].return_value = [PDF_FILE_1]
            mocks['read_all_from_path'].return_value = PDF_CONTENT_1
            configure_pipeline(p, opt, pipeline, app_config)

        step2.assert_called_with({
            'content': TEI_XML_CONTENT_1,
            'source_filename': PDF_FILE_1,
            'filename': PDF_FILE_1,
            'type': MimeTypes.TEI_XML
        })
        mocks['save_file_content'].assert_called_with(
            OUTPUT_XML_FILE_1,
            XML_CONTENT_1
        )

    def test_should_skip_item_causing_exception_and_increase_error_count(
            self, pipeline, app_config, file_list_args, mocks):

        opt = file_list_args

        step1 = _pdf_step()
        step1.side_effect = RuntimeError('doh1')

        pipeline.get_steps.return_value = [step1]

        with TestPipeline() as p:
            mocks['get_remaining_file_list_for_args'].return_value = [PDF_FILE_1]
            mocks['read_all_from_path'].return_value = PDF_CONTENT_1
            configure_pipeline(p, opt, pipeline, app_config)
            assert get_counter_value(
                p.run(), get_step_error_counter(step1)
            ) == 1

        mocks['save_file_content'].assert_not_called()

    def test_should_skip_step_if_data_type_doesnt_match_and_increase_ignored_count(
            self, pipeline, app_config, file_list_args, mocks):

        opt = file_list_args

        step1 = _convert_step(name='step1', supported_types={'other'})

        pipeline.get_steps.return_value = [step1]

        with TestPipeline() as p:
            mocks['get_remaining_file_list_for_args'].return_value = [PDF_FILE_1]
            mocks['read_all_from_path'].return_value = PDF_CONTENT_1
            configure_pipeline(p, opt, pipeline, app_config)
            assert get_counter_value(
                p.run(), get_step_ignored_counter(step1)
            ) == 1


class TestParseArgs:
    def test_should_parse_minimum_number_of_arguments(self, pipeline, app_config):
        parse_args(pipeline, app_config, MIN_ARGV)

    def test_should_not_resume_by_default(self, pipeline, app_config):
        args = parse_args(pipeline, app_config, MIN_ARGV)
        assert not args.resume

    def test_should_raise_error_if_no_source_argument_was_provided(self, pipeline, app_config):
        with pytest.raises(SystemExit):
            parse_args(pipeline, app_config, [
                '--data-path=' + BASE_DATA_PATH
            ])

    def test_should_allow_source_path_to_be_specified(self, pipeline, app_config):
        args = parse_args(pipeline, app_config, [
            '--data-path=' + BASE_DATA_PATH,
            '--source-path=' + PDF_PATH
        ])
        assert args.source_path == PDF_PATH

    def test_should_allow_source_file_list_and_column_to_be_specified(self, pipeline, app_config):
        args = parse_args(pipeline, app_config, [
            '--data-path=' + BASE_DATA_PATH,
            '--source-file-list=' + FILE_LIST_PATH,
            '--source-file-column=' + FILE_COLUMN
        ])
        assert args.source_file_list == FILE_LIST_PATH
        assert args.source_file_column == FILE_COLUMN

    def test_should_call_pipeline_add_arguments(self, pipeline, app_config):
        parse_args(pipeline, app_config, MIN_ARGV)
        pipeline.add_arguments.assert_called_with(ANY, app_config, MIN_ARGV)

    def test_should_parse_pipeline_args(self, pipeline, app_config):
        pipeline.add_arguments.side_effect = _add_test_args
        args = parse_args(pipeline, app_config, [
            '--data-path=' + BASE_DATA_PATH,
            '--source-file-list=' + FILE_LIST_PATH,
            '--source-file-column=' + FILE_COLUMN,
            '--pipeline=test',
            '--test-arg=123'
        ])
        assert args.test_arg == '123'


@pytest.mark.slow
class TestMainEndToEnd(BeamTest):
    def test_should_convert_single_file(self, temp_dir: Path, mock_server: MockServer):
        api_url = mock_server.add_response(
            '/api/convert', XML_CONTENT_1,
            mimetype=MimeTypes.JATS_XML,
            methods=('POST',)
        )
        LOGGER.debug('api_url: %s', api_url)
        source_path = temp_dir.joinpath('source')
        output_path = temp_dir.joinpath('output')
        source_path.mkdir(parents=True, exist_ok=True)
        source_path.joinpath('file1.pdf').write_bytes(PDF_CONTENT_1)
        source_path.joinpath('file-list.tsv').write_text('source_url\nfile1.pdf')
        output_file = output_path.joinpath('file1.xml')
        main([
            '--data-path=%s' % source_path,
            '--source-file-list=file-list.tsv',
            '--source-file-column=source_url',
            '--output-path=%s' % output_path,
            '--output-suffix=.xml',
            '--pipeline=api',
            '--api-url=%s' % api_url
        ], save_main_session=False)
        assert output_file.read_bytes() == XML_CONTENT_1
