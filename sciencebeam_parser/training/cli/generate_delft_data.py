import argparse
import logging
from pathlib import Path
from typing import List, Optional

from lxml import etree

import numpy as np

from sciencebeam_trainer_delft.sequence_labelling.tag_formatter import (
    TagOutputFormats,
    format_tag_result,
    get_tag_result
)

from sciencebeam_parser.utils.xml import get_text_content
from sciencebeam_parser.utils.tokenizer import get_tokenized_tokens


LOGGER = logging.getLogger(__name__)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        'ScienceBeam Parser: Generate DELFT Training Data'
    )
    parser.add_argument(
        '--model-name',
        type=str,
        required=True
    )
    parser.add_argument(
        '--tei-source-path',
        type=str,
        required=True
    )
    parser.add_argument(
        '--raw-source-path',
        type=str,
        required=True
    )
    parser.add_argument(
        '--delft-output-path',
        type=str,
        required=True
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    return parser.parse_args(argv)


def generate_delft_training_data(
    tei_source_path: str,
    delft_output_path: str
):
    LOGGER.debug('tei_source_path: %r', tei_source_path)
    tei_root = etree.parse(tei_source_path).getroot()
    token_texts = np.asarray(
        [get_tokenized_tokens(get_text_content(tei_root))],
        dtype='object'
    )
    token_labels = np.asarray(
        [['O'] * len(token_texts[0])],
        dtype='object'
    )
    features = np.full(shape=(1, len(token_texts[0]), 1), fill_value='0')
    tag_result = get_tag_result(texts=token_texts, labels=token_labels)
    LOGGER.debug('tag_result: %r', tag_result)
    LOGGER.debug('features: %r', features)
    LOGGER.debug('delft_output_path: %r', delft_output_path)
    Path(delft_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(delft_output_path).write_text(
        format_tag_result(
            tag_result=tag_result,
            output_format=TagOutputFormats.DATA,
            texts=token_texts,
            features=features
        ),
        encoding='utf-8'
    )


def run(args: argparse.Namespace):
    LOGGER.info('args: %r', args)
    generate_delft_training_data(
        tei_source_path=args.tei_source_path,
        delft_output_path=args.delft_output_path
    )


def main(argv: Optional[List[str]] = None):
    LOGGER.debug('argv: %r', argv)
    args = parse_args(argv)
    if args.debug:
        for name in [__name__, 'sciencebeam_parser', 'sciencebeam_trainer_delft']:
            logging.getLogger(name).setLevel('DEBUG')
    run(args)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()
