import argparse
import logging
from pathlib import Path
from typing import List, Optional


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
    LOGGER.info('output_path: %r', output_path)
    output_path.mkdir(parents=True, exist_ok=True)


def main(argv: Optional[List[str]] = None):
    LOGGER.debug('argv: %r', argv)
    args = parse_args(argv)
    run(args)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()
