from __future__ import absolute_import

import argparse
import logging

from sciencebeam.config.app_config import get_app_config

from sciencebeam.pipelines import (
    get_pipeline_for_configuration_and_args,
    add_pipeline_args
)

from sciencebeam.pipeline_runners.beam_pipeline_runner import (
    add_main_args,
    process_main_args
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

    LOGGER.info('args: %s', args)

    return args


def run(argv=None):
    config = get_app_config()

    pipeline = get_pipeline_for_configuration_and_args(config, argv=argv)

    parse_args(pipeline, config, argv)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    run()
