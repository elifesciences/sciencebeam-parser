import argparse
import logging
import os
from pathlib import Path
from glob import glob
from typing import List, Optional

from lxml import etree
from sciencebeam_trainer_delft.sequence_labelling.reader import load_data_crf_lines
from sciencebeam_parser.document.layout_document import LayoutDocument
from sciencebeam_parser.models.data import DocumentFeaturesContext, LabeledLayoutModelData
from sciencebeam_parser.models.segmentation.training_data import (
    SegmentationTeiTrainingDataGenerator
)
from sciencebeam_parser.processors.fulltext.models import FullTextModels
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
    parser.add_argument(
        '--use-model',
        action='store_true',
        help='Use configured models to pre-annotate training data'
    )
    return parser.parse_args(argv)


def generate_training_data_for_layout_document(
    layout_document: LayoutDocument,
    output_path: str,
    source_filename: str,
    document_features_context: DocumentFeaturesContext,
    fulltext_models: FullTextModels
):
    segmentation_model = fulltext_models.segmentation_model
    data_generator = segmentation_model.get_data_generator(
        document_features_context=document_features_context
    )
    training_data_generator = SegmentationTeiTrainingDataGenerator()
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
    data_lines = [
        model_data.data_line
        for model_data in model_data_list
    ]
    texts, features = load_data_crf_lines(data_lines)
    texts = texts.tolist()
    tag_result = segmentation_model.predict_labels(
        texts=texts, features=features, output_format=None
    )
    LOGGER.debug('texts: %r', texts)
    LOGGER.debug('data_lines: %r', data_lines)
    LOGGER.debug('tag_result: %r', tag_result)
    LOGGER.debug('model_data_list: %d', len(model_data_list))
    LOGGER.debug('tag_result[0]: %d', len(tag_result[0]))
    assert len(tag_result[0]) == len(model_data_list)
    labeled_model_data_list = [
        LabeledLayoutModelData.from_model_data(
            model_data,
            label=label
        )
        for model_data, (_, label) in zip(model_data_list, tag_result[0])
    ]
    training_tei_root = (
        training_data_generator
        .get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
    )
    Path(tei_file_path).write_bytes(
        etree.tostring(training_tei_root, pretty_print=True)
    )
    Path(data_file_path).write_text('\n'.join(
        model_data.data_line
        for model_data in model_data_list
    ), encoding='utf-8')


def generate_training_data_for_source_filename(
    source_filename: str,
    output_path: str,
    sciencebeam_parser: ScienceBeamParser
):
    with sciencebeam_parser.get_new_session() as session:
        source = session.get_source(source_filename, MediaTypes.PDF)
        layout_document = source.get_layout_document()
        generate_training_data_for_layout_document(
            layout_document=layout_document,
            output_path=output_path,
            source_filename=source_filename,
            document_features_context=DocumentFeaturesContext(
                sciencebeam_parser.app_features_context
            ),
            fulltext_models=sciencebeam_parser.fulltext_models
        )


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
