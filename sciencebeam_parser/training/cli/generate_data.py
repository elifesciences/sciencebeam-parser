import argparse
import logging
import os
from pathlib import Path
from typing import List, Optional

from lxml import etree

from sciencebeam_parser.models.segmentation.training_data import (
    SegmentationTeiTrainingDataGenerator
)
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
    training_data_generator = SegmentationTeiTrainingDataGenerator()
    with sciencebeam_parser.get_new_session() as session:
        source = session.get_source(args.source_path, MediaTypes.PDF)
        layout_document = source.get_layout_document()
        source_basename = os.path.basename(args.source_path)
        source_name = os.path.splitext(source_basename)[0]
        tei_file_path = output_path.joinpath(
            source_name + SegmentationTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        training_tei_root = training_data_generator.get_training_tei_xml_for_layout_document(
            layout_document=layout_document
        )
        tei_file_path.write_bytes(
            etree.tostring(training_tei_root, pretty_print=True)
        )


def main(argv: Optional[List[str]] = None):
    LOGGER.debug('argv: %r', argv)
    args = parse_args(argv)
    run(args)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()
