import argparse
import logging
import os
from glob import glob
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from lxml import etree

from sciencebeam_trainer_delft.sequence_labelling.reader import (
    load_data_crf_lines
)
from sciencebeam_trainer_delft.sequence_labelling.tag_formatter import (
    TagOutputFormats,
    format_tag_result
)

from sciencebeam_parser.models.segmentation.training_data import (
    SegmentationTrainingTeiParser
)
from sciencebeam_parser.models.header.training_data import (
    HeaderTrainingTeiParser
)
from sciencebeam_parser.models.training_data import TrainingTeiParser


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


def get_raw_file_for_tei_file(
    tei_file: str,
    raw_source_path: str
) -> str:
    tei_suffix = '.tei.xml'
    assert tei_file.endswith(tei_suffix)
    return os.path.join(raw_source_path, os.path.basename(tei_file[:-len(tei_suffix)]))


def get_raw_file_list_for_tei_file_list(
    tei_file_list: Iterable[str],
    raw_source_path: str
) -> Sequence[str]:
    return [
        get_raw_file_for_tei_file(tei_file, raw_source_path=raw_source_path)
        for tei_file in tei_file_list
    ]


def get_training_tei_parser_for_model_name(model_name: str) -> TrainingTeiParser:
    if model_name == 'segmentation':
        return SegmentationTrainingTeiParser()
    if model_name == 'header':
        return HeaderTrainingTeiParser()
    raise RuntimeError('unsupported model: %r' % model_name)


def generate_delft_training_data(  # pylint: disable=too-many-locals
    model_name: str,
    tei_source_path: str,
    raw_source_path: str,
    delft_output_path: str
):
    training_tei_parser = get_training_tei_parser_for_model_name(model_name)
    LOGGER.debug('tei_source_path: %r', tei_source_path)
    tei_file_list = glob(tei_source_path)
    if not tei_file_list:
        raise RuntimeError('no files found for file pattern %r' % tei_source_path)
    LOGGER.info('tei_file_list: %r', tei_file_list)
    raw_file_list = get_raw_file_list_for_tei_file_list(
        tei_file_list,
        raw_source_path=raw_source_path
    )
    LOGGER.info('raw_file_list: %r', raw_file_list)
    LOGGER.info('writing to : %r', delft_output_path)
    Path(delft_output_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(delft_output_path).open('w', encoding='utf-8') as data_fp:
        for document_index, (tei_file, raw_file) in enumerate(zip(tei_file_list, raw_file_list)):
            tei_root = etree.parse(tei_file).getroot()
            tag_result = training_tei_parser.parse_training_tei_to_tag_result(
                tei_root
            )
            LOGGER.debug('tag_result: %r', tag_result)
            with open(raw_file, 'r', encoding='utf-8') as raw_fp:
                texts, features = load_data_crf_lines(
                    raw_fp
                )
            assert len(texts) == len(tag_result)
            for doc_tokens, doc_tag_result in zip(texts, tag_result):
                assert len(doc_tokens) == len(doc_tag_result)
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
        model_name=args.model_name,
        tei_source_path=args.tei_source_path,
        raw_source_path=args.raw_source_path,
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
