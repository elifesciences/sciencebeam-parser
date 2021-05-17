import argparse
import logging
import os
from functools import partial
from typing import Callable, List

from sciencebeam_utils.beam_utils.files import find_matching_filenames_with_limit

from sciencebeam_utils.utils.file_path import (
    join_if_relative_path,
    get_output_file
)

from sciencebeam_utils.utils.file_list import (
    load_file_list
)

from sciencebeam_utils.tools.check_file_list import map_file_list_to_file_exists


LOGGER = logging.getLogger(__name__)


class DataProps:
    SOURCE_FILENAME = 'source_filename'
    FILENAME = 'filename'
    CONTENT = 'content'
    TYPE = 'type'


def add_batch_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        '--data-path', type=str, required=True,
        help='base data path'
    )

    source_group = parser.add_argument_group('source')
    source_one_of_group = source_group.add_mutually_exclusive_group(
        required=True
    )
    source_one_of_group.add_argument(
        '--source-path', type=str, required=False,
        help='path to source file(s), relative to data-path'
    )
    source_one_of_group.add_argument(
        '--source-file-list', type=str, required=False,
        help='path to source csv/tsv file list'
    )
    source_group.add_argument(
        '--source-file-column', type=str, required=False, default='url',
        help='the column of the source file list to use'
    )

    parser.add_argument(
        '--limit', type=int, required=False,
        help='limit the number of file pairs to process'
    )

    output_group = parser.add_argument_group('output')
    output_group.add_argument(
        '--output-path', required=False,
        help='Output directory to write results to.'
    )
    output_group.add_argument(
        '--output-suffix', required=False, default='.xml',
        help='Output file suffix to add to the filename (excluding the file extension).'
    )

    parser.add_argument(
        '--resume', action='store_true', default=False,
        help='resume conversion (skip files that already have an output file)'
    )

    parser.add_argument(
        '--debug', action='store_true', default=False,
        help='enable debug output'
    )


def process_batch_args(args):
    args.base_data_path = args.data_path.replace('/*/', '/')

    if not args.output_path:
        args.output_path = os.path.join(
            os.path.dirname(args.base_data_path),
            os.path.basename(args.base_data_path + '-results')
        )


def encode_if_text_type(data):
    return data.encode('utf-8') if isinstance(data, str) else data


def get_file_list_for_args(args: argparse.Namespace):
    if args.source_file_list:
        file_list_path = join_if_relative_path(args.base_data_path, args.source_file_list)
        return load_file_list(
            file_list_path, column=args.source_file_column, limit=args.limit
        )
    return list(find_matching_filenames_with_limit(
        join_if_relative_path(args.base_data_path, args.source_path), limit=args.limit
    ))


def get_file_list_without_output_file(
        file_list: List[str],
        get_output_file_for_source_url: Callable[[str], str]) -> List[str]:
    output_file_exists_list = map_file_list_to_file_exists([
        get_output_file_for_source_url(file_url)
        for file_url in file_list
    ])
    LOGGER.debug('output_file_exists_list: %s', output_file_exists_list)
    return [
        file_url
        for file_url, output_file_exists in zip(file_list, output_file_exists_list)
        if not output_file_exists
    ]


def get_output_file_for_source_file_fn(args):
    return partial(
        get_output_file,
        source_base_path=args.base_data_path,
        output_base_path=args.output_path,
        output_file_suffix=args.output_suffix
    )


def get_remaining_file_list_for_args(args: argparse.Namespace):
    file_list = get_file_list_for_args(args)
    LOGGER.debug('file_list: %s', file_list)

    if not file_list:
        LOGGER.warning('no files found')
        return file_list

    LOGGER.info('total number of files: %d', len(file_list))
    if args.resume:
        file_list = get_file_list_without_output_file(
            file_list,
            get_output_file_for_source_url=get_output_file_for_source_file_fn(args)
        )
        LOGGER.info('remaining number of files: %d', len(file_list))
    return file_list
