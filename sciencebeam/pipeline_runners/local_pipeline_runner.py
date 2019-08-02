from __future__ import absolute_import

import argparse
import logging
import concurrent.futures
from functools import partial
from mimetypes import guess_type
from typing import Callable, List

from sciencebeam_utils.beam_utils.io import (
    read_all_from_path,
    save_file_content
)

from sciencebeam_utils.beam_utils.files import find_matching_filenames_with_limit

from sciencebeam_utils.utils.file_path import (
    join_if_relative_path,
    get_output_file
)

from sciencebeam_utils.utils.file_list import (
    load_file_list
)

from sciencebeam_utils.tools.check_file_list import map_file_list_to_file_exists

from sciencebeam.utils.formatting import format_size

from sciencebeam.config.app_config import get_app_config

from sciencebeam.pipelines import Pipeline

from sciencebeam.pipelines import (
    get_pipeline_for_configuration_and_args,
    add_pipeline_args
)

from sciencebeam.pipeline_runners.beam_pipeline_runner import (
    process_main_args,
    encode_if_text_type,
    DataProps
)

from sciencebeam.pipeline_runners.simple_pipeline_runner import (
    SimplePipelineRunner
)

from sciencebeam.pipeline_runners.pipeline_runner_utils import (
    add_batch_args
)


LOGGER = logging.getLogger(__name__)


def add_num_workers_argument(parser: argparse.ArgumentParser):
    parser.add_argument(
        '--num-workers', '--num_workers',
        default=1,
        type=int,
        help='The number of workers.'
    )


def parse_args(pipeline, config, argv=None):
    parser = argparse.ArgumentParser()
    add_pipeline_args(parser)
    add_batch_args(parser)
    add_num_workers_argument(parser)
    pipeline.add_arguments(parser, config, argv)

    args = parser.parse_args(argv)

    if args.debug:
        logging.getLogger().setLevel('DEBUG')

    process_main_args(args)

    return args


def get_file_list_for_args(args: argparse.Namespace):
    if args.source_file_list:
        file_list_path = join_if_relative_path(args.base_data_path, args.source_file_list)
        return load_file_list(
            file_list_path, column=args.source_file_column, limit=args.limit
        )
    return list(find_matching_filenames_with_limit(
        join_if_relative_path(args.base_data_path, args.source_path), limit=args.limit
    ))


def get_output_file_for_source_file_fn(args):
    return partial(
        get_output_file,
        source_base_path=args.base_data_path,
        output_base_path=args.output_path,
        output_file_suffix=args.output_suffix
    )


def process_file(
        file_url: str, simple_runner: SimplePipelineRunner,
        get_output_file_for_source_url: Callable[[str], str]):
    output_file_url = get_output_file_for_source_url(
        file_url
    )
    file_content = read_all_from_path(file_url)
    LOGGER.info('read source content: %s (%s)', file_url, format_size(len(file_content)))
    data_type = guess_type(file_url)[0]
    LOGGER.debug('data_type: %s', data_type)
    result = simple_runner.convert(file_content, file_url, data_type)
    LOGGER.debug('result.keys: %s', result.keys())
    output_content = encode_if_text_type(result[DataProps.CONTENT])
    save_file_content(output_file_url, output_content)
    LOGGER.info('saved output to: %s (%s)', output_file_url, format_size(len(output_content)))


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


def run(args, config, pipeline: Pipeline):
    LOGGER.info('args: %s', args)
    file_list = get_file_list_for_args(args)
    LOGGER.debug('file_list: %s', file_list)

    if not file_list:
        LOGGER.warning('no files found')
        return

    simple_runner = SimplePipelineRunner(pipeline.get_steps(config, args))

    LOGGER.info('total number of files: %d', len(file_list))
    if args.resume:
        file_list = get_file_list_without_output_file(
            file_list,
            get_output_file_for_source_url=get_output_file_for_source_file_fn(args)
        )
        LOGGER.info('remaining number of files: %d', len(file_list))

    if not file_list:
        LOGGER.info('no files to process')
        return

    process_file_url = partial(
        process_file,
        simple_runner=simple_runner,
        get_output_file_for_source_url=get_output_file_for_source_file_fn(args)
    )

    num_workers = args.num_workers
    LOGGER.info('using %d workers', num_workers)
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_url = {
            executor.submit(process_file_url, url): url
            for url in file_list
        }
        LOGGER.debug('future_to_url: %s', future_to_url)
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.warning('%r generated an exception: %s', url, exc)


def main(argv=None):
    config = get_app_config()

    pipeline = get_pipeline_for_configuration_and_args(config, argv=argv)

    args = parse_args(pipeline, config, argv)
    run(args, config=config, pipeline=pipeline)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()
