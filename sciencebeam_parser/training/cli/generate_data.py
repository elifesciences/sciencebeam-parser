import argparse
import logging
import os
from pathlib import Path
from glob import glob
from typing import List, Optional

from lxml import etree
from sciencebeam_parser.models.data import DocumentFeaturesContext

from sciencebeam_parser.models.segmentation.data import (
    SegmentationDataGenerator
)
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


def generate_training_data_for_source_filename(
    source_filename: str,
    output_path: str,
    sciencebeam_parser: ScienceBeamParser
):
    data_generator = SegmentationDataGenerator(
        document_features_context=DocumentFeaturesContext(
            sciencebeam_parser.app_features_context
        ),
        use_first_token_of_block=True
    )
    training_data_generator = SegmentationTeiTrainingDataGenerator()
    with sciencebeam_parser.get_new_session() as session:
        source = session.get_source(source_filename, MediaTypes.PDF)
        layout_document = source.get_layout_document()
        source_basename = os.path.basename(source_filename)
        source_name = os.path.splitext(source_basename)[0]
        tei_file_path = os.path.join(
            output_path,
            source_name + SegmentationTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        data_file_path = os.path.join(
            output_path,
            source_name + SegmentationTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        model_data_list = list(data_generator.iter_model_data_for_layout_document(
            layout_document
        ))
        training_tei_root = (
            training_data_generator
            .get_training_tei_xml_for_model_data_iterable(
                model_data_list
            )
        )
        Path(tei_file_path).write_bytes(
            etree.tostring(training_tei_root, pretty_print=True)
        )
        Path(data_file_path).write_text('\n'.join(
            model_data.data_line
            for model_data in model_data_list
        ), encoding='utf-8')


def run(args: argparse.Namespace):
    LOGGER.info('args: %r', args)
    output_path = args.output_path
    config = AppConfig.load_yaml(
        DEFAULT_CONFIG_FILE
    )
    sciencebeam_parser = ScienceBeamParser.from_config(config)
    LOGGER.info('output_path: %r', output_path)
    os.makedirs(output_path, exist_ok=True)
    for source_filename in glob(args.source_path):
        generate_training_data_for_source_filename(
            source_filename,
            output_path=output_path,
            sciencebeam_parser=sciencebeam_parser
        )


def main(argv: Optional[List[str]] = None):
    LOGGER.debug('argv: %r', argv)
    args = parse_args(argv)
    run(args)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()
