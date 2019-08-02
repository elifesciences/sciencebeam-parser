from unittest.mock import patch, MagicMock

import pytest

import sciencebeam.pipeline_runners.pipeline_runner_utils as pipeline_runner_utils_module
from sciencebeam.pipeline_runners.pipeline_runner_utils import (
    get_remaining_file_list_for_args
)


BASE_TEST_PATH = '/tmp/test/conversion-pipeline'
BASE_DATA_PATH = BASE_TEST_PATH + '/data'
PDF_PATH = '*/*.pdf'
FILE_LIST_PATH = 'file-list.csv'
FILE_COLUMN = 'column1'

REL_PDF_FILE_WITHOUT_EXT_1 = '1/file'
PDF_FILE_1 = BASE_DATA_PATH + '/' + REL_PDF_FILE_WITHOUT_EXT_1 + '.pdf'

OUTPUT_PATH = BASE_TEST_PATH + '/out'
OUTPUT_SUFFIX = '.xml'


@pytest.fixture(name='load_file_list_mock', autouse=True)
def _load_file_list_mock():
    with patch.object(pipeline_runner_utils_module, 'load_file_list') as mock:
        yield mock


@pytest.fixture(name='find_matching_filenames_with_limit_mock', autouse=True)
def _find_matching_filenames_with_limit_mock():
    with patch.object(pipeline_runner_utils_module, 'find_matching_filenames_with_limit') as mock:
        yield mock


@pytest.fixture(name='map_file_list_to_file_exists_mock', autouse=True)
def _map_file_list_to_file_exists_mock():
    with patch.object(pipeline_runner_utils_module, 'map_file_list_to_file_exists') as mock:
        mock.side_effect = lambda file_list: [False] * len(file_list)
        yield mock


@pytest.fixture(name='args')
def get_default_args():
    opt = MagicMock()
    opt.base_data_path = BASE_DATA_PATH
    opt.output_path = OUTPUT_PATH
    opt.output_suffix = OUTPUT_SUFFIX
    opt.limit = None
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


class TestGetRemainingFileListForArgs:
    def test_should_pass_file_pattern_to_find_files(
            self, file_path_args,
            find_matching_filenames_with_limit_mock: MagicMock):

        find_matching_filenames_with_limit_mock.return_value = [PDF_FILE_1]
        assert (
            get_remaining_file_list_for_args(file_path_args)
            == find_matching_filenames_with_limit_mock.return_value
        )

        find_matching_filenames_with_limit_mock.assert_called_with(
            BASE_DATA_PATH + '/' + PDF_PATH,
            limit=file_path_args.limit
        )

    def test_should_pass_file_list_and_limit_to_load_file_list(
            self, file_list_args,
            load_file_list_mock: MagicMock):

        opt = file_list_args
        opt.limit = 100
        load_file_list_mock.return_value = [PDF_FILE_1]
        assert (
            get_remaining_file_list_for_args(opt)
            == load_file_list_mock.return_value
        )

        load_file_list_mock.assert_called_with(
            opt.source_file_list, column=opt.source_file_column, limit=opt.limit
        )
