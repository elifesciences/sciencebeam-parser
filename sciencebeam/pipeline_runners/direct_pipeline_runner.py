from __future__ import absolute_import

import argparse
import logging
from functools import partial
from mimetypes import guess_type
from typing import Callable

from sciencebeam_utils.beam_utils.io import (
    read_all_from_path,
    save_file_content
)

from sciencebeam_utils.utils.file_path import (
    join_if_relative_path,
    get_output_file
)

from sciencebeam_utils.utils.file_list import (
    load_file_list
)

from sciencebeam.config.app_config import get_app_config

from sciencebeam.pipelines import Pipeline

from sciencebeam.pipelines import (
    get_pipeline_for_configuration_and_args,
    add_pipeline_args
)

from sciencebeam.pipeline_runners.beam_pipeline_runner import (
    add_main_args,
    process_main_args,
    encode_if_text_type,
    DataProps
)

from sciencebeam.pipeline_runners.simple_pipeline_runner import (
    SimplePipelineRunner
)


LOGGER = logging.getLogger(__name__)


def parse_args(pipeline, config, argv=None):
    parser = argparse.ArgumentParser()
    add_pipeline_args(parser)
    add_main_args(parser)
    pipeline.add_arguments(parser, config, argv)

    args = parser.parse_args(argv)

    if args.debug:
        logging.getLogger().setLevel('DEBUG')

    process_main_args(args)

    return args


def load_file_list_for_args(args: argparse.Namespace):
    file_list_path = join_if_relative_path(args.base_data_path, args.source_file_list)
    return load_file_list(
        file_list_path, column=args.source_file_column, limit=args.limit
    )


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
    LOGGER.debug('file_content: %s', file_content)
    data_type = guess_type(file_url)[0]
    LOGGER.debug('data_type: %s', data_type)
    result = simple_runner.convert(file_content, file_url, data_type)
    LOGGER.debug('result: %s', result)
    save_file_content(
        output_file_url,
        encode_if_text_type(result[DataProps.CONTENT])
    )


def run(args, config, pipeline: Pipeline):
    LOGGER.info('args: %s', args)
    file_list = load_file_list_for_args(args)
    LOGGER.debug('file_list: %s', file_list)
    simple_runner = SimplePipelineRunner(pipeline.get_steps(config, args))
    for file_url in file_list:
        process_file(
            file_url, simple_runner=simple_runner,
            get_output_file_for_source_url=get_output_file_for_source_file_fn(args)
        )


def main(argv=None):
    config = get_app_config()

    pipeline = get_pipeline_for_configuration_and_args(config, argv=argv)

    args = parse_args(pipeline, config, argv)
    run(args, config=config, pipeline=pipeline)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()
