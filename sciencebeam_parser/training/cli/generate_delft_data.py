import argparse
import logging
from glob import glob
from pathlib import Path
from typing import List, Optional, Tuple

from lxml import etree

import numpy as np

from sciencebeam_trainer_delft.sequence_labelling.tag_formatter import (
    TagOutputFormats,
    format_tag_result
)

from sciencebeam_parser.models.segmentation.training_data import (
    SegmentationTrainingTeiParser
)


LOGGER = logging.getLogger(__name__)


def parse_segmentation_training_tei_to_tag_result(
    tei_root: etree.ElementBase
) -> List[List[Tuple[str, str]]]:
    return SegmentationTrainingTeiParser().parse_training_tei_to_tag_result(tei_root)


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
    tei_file_list = glob(tei_source_path)
    if not tei_file_list:
        raise RuntimeError('no files found for file pattern %r' % tei_source_path)
    LOGGER.info('tei_file_list: %r', tei_file_list)
    LOGGER.info('writing to : %r', delft_output_path)
    Path(delft_output_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(delft_output_path).open('w', encoding='utf-8') as data_fp:
        for document_index, tei_file in enumerate(tei_file_list):
            tei_root = etree.parse(tei_file).getroot()
            tag_result = parse_segmentation_training_tei_to_tag_result(
                tei_root
            )
            LOGGER.debug('tag_result: %r', tag_result)
            features = np.full(shape=(1, len(tag_result[0]), 1), fill_value='0')
            LOGGER.debug('features: %r', features)
            if document_index > 0:
                data_fp.write('\n\n')
            data_fp.write(
                format_tag_result(
                    tag_result=tag_result,
                    output_format=TagOutputFormats.DATA,
                    texts=None,
                    features=features
                )
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
