import argparse
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from glob import glob
from typing import Iterable, List, Optional, Sequence

from lxml import etree
from sciencebeam_trainer_delft.sequence_labelling.reader import load_data_crf_lines
from sciencebeam_parser.document.layout_document import LayoutDocument
from sciencebeam_parser.document.semantic_document import (
    SemanticMixedContentWrapper,
    SemanticRawAffiliationAddress
)
from sciencebeam_parser.models.data import (
    DocumentFeaturesContext,
    LabeledLayoutModelData,
    LayoutModelData
)
from sciencebeam_parser.models.model import (
    LayoutDocumentLabelResult,
    LayoutModelLabel,
    Model,
    iter_data_lines_for_model_data_iterables,
    iter_labeled_layout_token_for_layout_model_label
)
from sciencebeam_parser.models.segmentation.training_data import (
    SegmentationTeiTrainingDataGenerator
)
from sciencebeam_parser.models.header.training_data import HeaderTeiTrainingDataGenerator
from sciencebeam_parser.models.affiliation_address.training_data import (
    AffiliationAddressTeiTrainingDataGenerator
)
from sciencebeam_parser.processors.fulltext.models import FullTextModels
from sciencebeam_parser.resources.default_config import DEFAULT_CONFIG_FILE
from sciencebeam_parser.config.config import AppConfig
from sciencebeam_parser.app.parser import ScienceBeamParser
from sciencebeam_parser.utils.media_types import MediaTypes


LOGGER = logging.getLogger(__name__)


@dataclass
class ModelResultCache:
    segmentation_label_model_data_list: Optional[Sequence[LabeledLayoutModelData]] = None
    header_label_model_data_list: Optional[Sequence[LabeledLayoutModelData]] = None


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


def get_labeled_model_data_list_list(
    model_data_list_list: Sequence[Sequence[LayoutModelData]],
    model: Model
) -> Sequence[Sequence[LabeledLayoutModelData]]:
    if not model_data_list_list:
        return []
    data_lines = list(iter_data_lines_for_model_data_iterables(
        model_data_list_list
    ))
    texts, features = load_data_crf_lines(data_lines)
    texts = texts.tolist()
    tag_result = model.predict_labels(
        texts=texts, features=features, output_format=None
    )
    LOGGER.debug('texts: %r', texts)
    LOGGER.debug('data_lines: %r', data_lines)
    LOGGER.debug('tag_result: %r', tag_result)
    LOGGER.debug('model_data_list_list[0]: %d', len(model_data_list_list[0]))
    LOGGER.debug('tag_result[0]: %d', len(tag_result[0]))
    assert len(tag_result[0]) == len(model_data_list_list[0])
    labeled_model_data_list_list = [
        [
            LabeledLayoutModelData.from_model_data(
                model_data,
                label=label
            )
            for model_data, (_, label) in zip(model_data_list, tag_result[0])
        ]
        for model_data_list in model_data_list_list
    ]
    return labeled_model_data_list_list


def get_labeled_model_data_list(
    model_data_list: Sequence[LayoutModelData],
    model: Model
) -> Sequence[LabeledLayoutModelData]:
    return get_labeled_model_data_list_list(
        [model_data_list],
        model=model
    )[0]


def get_labeled_model_data_list_for_layout_document(
    layout_document: LayoutDocument,
    model: Model,
    document_features_context: DocumentFeaturesContext
) -> Sequence[LabeledLayoutModelData]:
    data_generator = model.get_data_generator(
        document_features_context=document_features_context
    )
    model_data_list: Sequence[LayoutModelData] = list(
        data_generator.iter_model_data_for_layout_document(layout_document)
    )
    return get_labeled_model_data_list(
        model_data_list,
        model=model
    )


def get_layout_model_label_for_labeled_model_data(
    labeled_model_data: LabeledLayoutModelData
) -> LayoutModelLabel:
    return LayoutModelLabel(
        label=labeled_model_data.label or '',
        label_token_text=labeled_model_data.label_token_text,
        layout_line=labeled_model_data.layout_line,
        layout_token=labeled_model_data.layout_token
    )


def iter_layout_model_label_for_labeled_model_data_list(
    labeled_model_data_iterable: Iterable[LabeledLayoutModelData],
) -> Iterable[LayoutModelLabel]:
    return (
        get_layout_model_label_for_labeled_model_data(labeled_model_data)
        for labeled_model_data in labeled_model_data_iterable
    )


def get_layout_document_label_result_for_labeled_model_data_list(
    labeled_model_data_iterable: Iterable[LabeledLayoutModelData],
    layout_document: LayoutDocument
) -> LayoutDocumentLabelResult:
    return LayoutDocumentLabelResult(
        layout_document=layout_document,
        layout_model_label_iterable=iter_layout_model_label_for_labeled_model_data_list(
            labeled_model_data_iterable
        )
    )


def get_segmentation_label_model_data_list_for_layout_document(
    layout_document: LayoutDocument,
    segmentation_model: Model,
    document_features_context: DocumentFeaturesContext,
    model_result_cache: ModelResultCache
) -> Sequence[LabeledLayoutModelData]:
    segmentation_label_model_data_list = model_result_cache.segmentation_label_model_data_list
    if segmentation_label_model_data_list is not None:
        return segmentation_label_model_data_list
    segmentation_label_model_data_list = get_labeled_model_data_list_for_layout_document(
        layout_document,
        model=segmentation_model,
        document_features_context=document_features_context
    )
    model_result_cache.segmentation_label_model_data_list = segmentation_label_model_data_list
    return segmentation_label_model_data_list


def get_header_label_model_data_list_for_layout_document(
    layout_document: LayoutDocument,
    header_model: Model,
    document_features_context: DocumentFeaturesContext,
    model_result_cache: ModelResultCache
) -> Sequence[LabeledLayoutModelData]:
    header_label_model_data_list = model_result_cache.header_label_model_data_list
    if header_label_model_data_list is not None:
        return header_label_model_data_list
    header_label_model_data_list = get_labeled_model_data_list_for_layout_document(
        layout_document,
        model=header_model,
        document_features_context=document_features_context
    )
    model_result_cache.header_label_model_data_list = header_label_model_data_list
    return header_label_model_data_list


def generate_segmentation_training_data_for_layout_document(  # pylint: disable=too-many-locals
    layout_document: LayoutDocument,
    output_path: str,
    source_filename: str,
    document_features_context: DocumentFeaturesContext,
    fulltext_models: FullTextModels,
    use_model: bool,
    model_result_cache: ModelResultCache
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
    model_data_list: Sequence[LayoutModelData]
    if use_model:
        model_data_list = (
            get_segmentation_label_model_data_list_for_layout_document(
                layout_document,
                segmentation_model=segmentation_model,
                document_features_context=document_features_context,
                model_result_cache=model_result_cache
            )
        )
    else:
        model_data_list = list(
            data_generator.iter_model_data_for_layout_document(layout_document)
        )
    training_tei_root = (
        training_data_generator
        .get_training_tei_xml_for_model_data_iterable(
            model_data_list
        )
    )
    LOGGER.info('writing training tei to: %r', tei_file_path)
    Path(tei_file_path).write_bytes(
        etree.tostring(training_tei_root, pretty_print=True)
    )
    LOGGER.info('writing training raw data to: %r', data_file_path)
    Path(data_file_path).write_text('\n'.join(
        model_data.data_line
        for model_data in model_data_list
    ), encoding='utf-8')


def generate_header_training_data_for_layout_document(  # pylint: disable=too-many-locals
    layout_document: LayoutDocument,
    output_path: str,
    source_filename: str,
    document_features_context: DocumentFeaturesContext,
    fulltext_models: FullTextModels,
    use_model: bool,
    model_result_cache: ModelResultCache
):
    segmentation_model = fulltext_models.segmentation_model
    header_model = fulltext_models.header_model
    data_generator = header_model.get_data_generator(
        document_features_context=document_features_context
    )
    training_data_generator = HeaderTeiTrainingDataGenerator()
    source_basename = os.path.basename(source_filename)
    source_name = os.path.splitext(source_basename)[0]
    tei_file_path = os.path.join(
        output_path,
        source_name + HeaderTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
    )
    data_file_path = os.path.join(
        output_path,
        source_name + HeaderTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
    )
    segmentation_label_model_data_list = (
        get_segmentation_label_model_data_list_for_layout_document(
            layout_document,
            segmentation_model=segmentation_model,
            document_features_context=document_features_context,
            model_result_cache=model_result_cache
        )
    )
    segmentation_label_result = get_layout_document_label_result_for_labeled_model_data_list(
        labeled_model_data_iterable=segmentation_label_model_data_list,
        layout_document=layout_document
    )
    header_layout_document = segmentation_label_result.get_filtered_document_by_label(
        '<header>'
    ).remove_empty_blocks()
    model_data_list: Sequence[LayoutModelData]
    if use_model:
        model_data_list = (
            get_header_label_model_data_list_for_layout_document(
                header_layout_document,
                header_model=header_model,
                document_features_context=document_features_context,
                model_result_cache=model_result_cache
            )
        )
    else:
        model_data_list = list(
            data_generator.iter_model_data_for_layout_document(header_layout_document)
        )
    training_tei_root = (
        training_data_generator
        .get_training_tei_xml_for_model_data_iterable(
            model_data_list
        )
    )
    LOGGER.info('writing training tei to: %r', tei_file_path)
    Path(tei_file_path).write_bytes(
        etree.tostring(training_tei_root, pretty_print=True)
    )
    LOGGER.info('writing training raw data to: %r', data_file_path)
    Path(data_file_path).write_text('\n'.join(
        model_data.data_line
        for model_data in model_data_list
    ), encoding='utf-8')


def generate_aff_address_training_data_for_layout_document(  # pylint: disable=too-many-locals
    layout_document: LayoutDocument,
    output_path: str,
    source_filename: str,
    document_features_context: DocumentFeaturesContext,
    fulltext_models: FullTextModels,
    use_model: bool,
    model_result_cache: ModelResultCache
):
    segmentation_model = fulltext_models.segmentation_model
    header_model = fulltext_models.header_model
    affiliation_address_model = fulltext_models.affiliation_address_model
    data_generator = affiliation_address_model.get_data_generator(
        document_features_context=document_features_context
    )
    training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
    source_basename = os.path.basename(source_filename)
    source_name = os.path.splitext(source_basename)[0]
    tei_file_path = os.path.join(
        output_path,
        source_name + AffiliationAddressTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
    )
    segmentation_label_model_data_list = (
        get_segmentation_label_model_data_list_for_layout_document(
            layout_document,
            segmentation_model=segmentation_model,
            document_features_context=document_features_context,
            model_result_cache=model_result_cache
        )
    )
    segmentation_label_result = get_layout_document_label_result_for_labeled_model_data_list(
        labeled_model_data_iterable=segmentation_label_model_data_list,
        layout_document=layout_document
    )
    header_layout_document = segmentation_label_result.get_filtered_document_by_label(
        '<header>'
    ).remove_empty_blocks()
    header_model_data_list = (
        get_header_label_model_data_list_for_layout_document(
            header_layout_document,
            header_model=header_model,
            document_features_context=document_features_context,
            model_result_cache=model_result_cache
        )
    )
    header_labeled_layout_tokens = list(iter_labeled_layout_token_for_layout_model_label(
        iter_layout_model_label_for_labeled_model_data_list(
            header_model_data_list
        )
    ))
    semantic_raw_aff_address_list = list(
        SemanticMixedContentWrapper(list(
            header_model.iter_semantic_content_for_labeled_layout_tokens(
                header_labeled_layout_tokens
            )
        )).iter_by_type(SemanticRawAffiliationAddress)
    )
    LOGGER.info('semantic_raw_aff_address_list count: %d', len(semantic_raw_aff_address_list))

    model_data_list_list: Sequence[Sequence[LayoutModelData]] = []
    if semantic_raw_aff_address_list:
        aff_layout_documents = [
            LayoutDocument.for_blocks(
                list(semantic_raw_aff_address.iter_blocks())
            )
            for semantic_raw_aff_address in semantic_raw_aff_address_list
        ]
        model_data_list_list = [
            list(
                data_generator.iter_model_data_for_layout_document(aff_layout_document)
            )
            for aff_layout_document in aff_layout_documents
        ]
        if use_model:
            model_data_list_list = get_labeled_model_data_list_list(
                model_data_list_list,
                model=affiliation_address_model
            )
    training_tei_root = (
        training_data_generator
        .get_training_tei_xml_for_multiple_model_data_iterables(
            model_data_list_list
        )
    )
    LOGGER.info('writing training tei to: %r', tei_file_path)
    Path(tei_file_path).write_bytes(
        etree.tostring(training_tei_root, pretty_print=True)
    )


def generate_training_data_for_layout_document(
    layout_document: LayoutDocument,
    output_path: str,
    source_filename: str,
    document_features_context: DocumentFeaturesContext,
    fulltext_models: FullTextModels,
    use_model: bool
):
    model_result_cache = ModelResultCache()
    generate_segmentation_training_data_for_layout_document(
        layout_document=layout_document,
        output_path=output_path,
        source_filename=source_filename,
        document_features_context=document_features_context,
        fulltext_models=fulltext_models,
        use_model=use_model,
        model_result_cache=model_result_cache
    )
    generate_header_training_data_for_layout_document(
        layout_document=layout_document,
        output_path=output_path,
        source_filename=source_filename,
        document_features_context=document_features_context,
        fulltext_models=fulltext_models,
        use_model=use_model,
        model_result_cache=model_result_cache
    )
    generate_aff_address_training_data_for_layout_document(
        layout_document=layout_document,
        output_path=output_path,
        source_filename=source_filename,
        document_features_context=document_features_context,
        fulltext_models=fulltext_models,
        use_model=use_model,
        model_result_cache=model_result_cache
    )


def generate_training_data_for_source_filename(
    source_filename: str,
    output_path: str,
    sciencebeam_parser: ScienceBeamParser,
    use_model: bool
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
            fulltext_models=sciencebeam_parser.fulltext_models,
            use_model=use_model
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
            sciencebeam_parser=sciencebeam_parser,
            use_model=args.use_model
        )


def main(argv: Optional[List[str]] = None):
    LOGGER.debug('argv: %r', argv)
    args = parse_args(argv)
    run(args)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()
