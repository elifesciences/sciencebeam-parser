import argparse
import logging
from pathlib import Path
from typing import List, Optional

from sciencebeam_parser.resources.default_config import DEFAULT_CONFIG_FILE
from sciencebeam_parser.config.config import AppConfig
from sciencebeam_parser.app.parser import ScienceBeamParser
from sciencebeam_parser.utils.media_types import MediaTypes


LOGGER = logging.getLogger(__name__)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        'ScienceBeam Parser: Generate Training Data'
    )
    parser.add_argument(
        '--model',
        type=str,
        required=True
    )
    parser.add_argument(
        '--source-path',
        type=str,
        required=True
    )
    parser.add_argument(
        '--output-path',
        type=str,
        required=True
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace):
    LOGGER.info('args: %r', args)
    output_path = Path(args.output_path)
    config = AppConfig.load_yaml(
        DEFAULT_CONFIG_FILE
    )
    sciencebeam_parser = ScienceBeamParser.from_config(config)
    LOGGER.info('output_path: %r', output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    with sciencebeam_parser.get_new_session() as session:
        source = session.get_source(args.source_path, MediaTypes.PDF)
        _layout_document = source.lazy_parsed_layout_document.get().layout_document


def main(argv: Optional[List[str]] = None):
    LOGGER.debug('argv: %r', argv)
    args = parse_args(argv)
    run(args)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()
