# pylint: disable=too-many-lines
from abc import ABC, abstractmethod
import argparse
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from glob import glob
from typing import Iterable, List, Optional, Sequence

from lxml import etree

from sciencebeam_parser.document.layout_document import LayoutDocument
from sciencebeam_parser.document.semantic_document import (
    SemanticMixedContentWrapper,
    SemanticRawAffiliationAddress,
    SemanticRawFigure,
    SemanticRawReference,
    SemanticRawReferenceText
)
from sciencebeam_parser.models.data import (
    DocumentFeaturesContext,
    LabeledLayoutModelData,
    LayoutModelData
)
from sciencebeam_parser.models.fulltext.training_data import FullTextTeiTrainingDataGenerator
from sciencebeam_parser.models.model import (
    LayoutDocumentLabelResult,
    LayoutModelLabel,
    Model,
    iter_data_lines_for_model_data_iterables,
    iter_labeled_layout_token_for_layout_model_label
)
from sciencebeam_parser.models.reference_segmenter.training_data import (
    ReferenceSegmenterTeiTrainingDataGenerator
)
from sciencebeam_parser.models.citation.training_data import (
    CitationTeiTrainingDataGenerator
)
from sciencebeam_parser.models.segmentation.training_data import (
    SegmentationTeiTrainingDataGenerator
)
from sciencebeam_parser.models.header.training_data import HeaderTeiTrainingDataGenerator
from sciencebeam_parser.models.affiliation_address.training_data import (
    AffiliationAddressTeiTrainingDataGenerator
)
from sciencebeam_parser.models.figure.training_data import (
    FigureTeiTrainingDataGenerator
)
from sciencebeam_parser.models.training_data import AbstractTeiTrainingDataGenerator
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
    fulltext_label_model_data_list: Optional[Sequence[LabeledLayoutModelData]] = None
    reference_segmenter_label_model_data_list: Optional[Sequence[LabeledLayoutModelData]] = None


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
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    return parser.parse_args(argv)


def get_labeled_model_data_list_list(
    model_data_list_list: Sequence[Sequence[LayoutModelData]],
    model: Model
) -> Sequence[Sequence[LabeledLayoutModelData]]:
    return list(
        model.iter_labeled_model_data_list_for_model_data_list_iterable(
            model_data_list_list
        )
    )


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


def get_fulltext_label_model_data_list_for_layout_document(
    layout_document: LayoutDocument,
    fulltext_model: Model,
    document_features_context: DocumentFeaturesContext,
    model_result_cache: ModelResultCache
) -> Sequence[LabeledLayoutModelData]:
    fulltext_label_model_data_list = model_result_cache.fulltext_label_model_data_list
    if fulltext_label_model_data_list is not None:
        return fulltext_label_model_data_list
    fulltext_label_model_data_list = get_labeled_model_data_list_for_layout_document(
        layout_document,
        model=fulltext_model,
        document_features_context=document_features_context
    )
    model_result_cache.fulltext_label_model_data_list = fulltext_label_model_data_list
    return fulltext_label_model_data_list


def get_reference_segmenter_label_model_data_list_for_layout_document(
    layout_document: LayoutDocument,
    reference_segmenter_model: Model,
    document_features_context: DocumentFeaturesContext,
    model_result_cache: ModelResultCache
) -> Sequence[LabeledLayoutModelData]:
    reference_segmenter_label_model_data_list = (
        model_result_cache.reference_segmenter_label_model_data_list
    )
    if reference_segmenter_label_model_data_list is not None:
        return reference_segmenter_label_model_data_list
    reference_segmenter_label_model_data_list = get_labeled_model_data_list_for_layout_document(
        layout_document,
        model=reference_segmenter_model,
        document_features_context=document_features_context
    )
    model_result_cache.reference_segmenter_label_model_data_list = (
        reference_segmenter_label_model_data_list
    )
    return reference_segmenter_label_model_data_list


class AbstractModelTrainingDataGenerator(ABC):
    def __init__(
        self,
        output_path: str,
        source_filename: str,
        document_features_context: DocumentFeaturesContext,
        fulltext_models: FullTextModels,
        use_model: bool,
        model_result_cache: ModelResultCache,
        training_data_generator: AbstractTeiTrainingDataGenerator
    ):
        self.output_path = output_path
        self.source_filename = source_filename
        self.document_features_context = document_features_context
        self.fulltext_models = fulltext_models
        self.use_model = use_model
        self.model_result_cache = model_result_cache
        self.source_basename = os.path.basename(source_filename)
        self.source_name = os.path.splitext(self.source_basename)[0]
        self.training_data_generator = training_data_generator
        self.tei_file_path = self._get_file_path_with_suffix(
            self.training_data_generator.get_default_tei_filename_suffix()
        )
        self.data_file_path = self._get_file_path_with_suffix(
            self.training_data_generator.get_default_data_filename_suffix()
        )

    def _get_file_path_with_suffix(self, suffix: Optional[str]) -> Optional[str]:
        if not suffix:
            return None
        return os.path.join(self.output_path, self.source_name + suffix)

    @abstractmethod
    def generate_data_for_layout_document(
        self,
        layout_document: LayoutDocument
    ):
        pass


class SegmentationModelTrainingDataGenerator(AbstractModelTrainingDataGenerator):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            training_data_generator=SegmentationTeiTrainingDataGenerator()
        )

    def generate_data_for_layout_document(
        self,
        layout_document: LayoutDocument
    ):
        assert self.tei_file_path
        segmentation_model = self.fulltext_models.segmentation_model
        data_generator = segmentation_model.get_data_generator(
            document_features_context=self.document_features_context
        )
        training_data_generator = SegmentationTeiTrainingDataGenerator()
        model_data_list: Sequence[LayoutModelData]
        if self.use_model:
            model_data_list = (
                get_segmentation_label_model_data_list_for_layout_document(
                    layout_document,
                    segmentation_model=segmentation_model,
                    document_features_context=self.document_features_context,
                    model_result_cache=self.model_result_cache
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
        LOGGER.info('writing training tei to: %r', self.tei_file_path)
        Path(self.tei_file_path).write_bytes(
            etree.tostring(training_tei_root, pretty_print=True)
        )
        if self.data_file_path:
            LOGGER.info('writing training raw data to: %r', self.data_file_path)
            Path(self.data_file_path).write_text('\n'.join(
                model_data.data_line
                for model_data in model_data_list
            ), encoding='utf-8')


class HeaderModelTrainingDataGenerator(AbstractModelTrainingDataGenerator):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            training_data_generator=HeaderTeiTrainingDataGenerator()
        )

    def generate_data_for_layout_document(
        self,
        layout_document: LayoutDocument
    ):
        assert self.tei_file_path
        segmentation_model = self.fulltext_models.segmentation_model
        header_model = self.fulltext_models.header_model
        data_generator = header_model.get_data_generator(
            document_features_context=self.document_features_context
        )
        segmentation_label_model_data_list = (
            get_segmentation_label_model_data_list_for_layout_document(
                layout_document,
                segmentation_model=segmentation_model,
                document_features_context=self.document_features_context,
                model_result_cache=self.model_result_cache
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
        if self.use_model:
            model_data_list = (
                get_header_label_model_data_list_for_layout_document(
                    header_layout_document,
                    header_model=header_model,
                    document_features_context=self.document_features_context,
                    model_result_cache=self.model_result_cache
                )
            )
        else:
            model_data_list = list(
                data_generator.iter_model_data_for_layout_document(header_layout_document)
            )
        training_tei_root = (
            self.training_data_generator
            .get_training_tei_xml_for_model_data_iterable(
                model_data_list
            )
        )
        LOGGER.info('writing training tei to: %r', self.tei_file_path)
        Path(self.tei_file_path).write_bytes(
            etree.tostring(training_tei_root, pretty_print=True)
        )
        LOGGER.info('writing training raw data to: %r', self.data_file_path)
        if self.data_file_path:
            Path(self.data_file_path).write_text('\n'.join(
                model_data.data_line
                for model_data in model_data_list
            ), encoding='utf-8')


class AffiliationAddressModelTrainingDataGenerator(AbstractModelTrainingDataGenerator):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            training_data_generator=AffiliationAddressTeiTrainingDataGenerator()
        )

    def generate_data_for_layout_document(   # pylint: disable=too-many-locals
        self,
        layout_document: LayoutDocument
    ):
        assert self.tei_file_path
        segmentation_model = self.fulltext_models.segmentation_model
        header_model = self.fulltext_models.header_model
        affiliation_address_model = self.fulltext_models.affiliation_address_model
        data_generator = affiliation_address_model.get_data_generator(
            document_features_context=self.document_features_context
        )
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        segmentation_label_model_data_list = (
            get_segmentation_label_model_data_list_for_layout_document(
                layout_document,
                segmentation_model=segmentation_model,
                document_features_context=self.document_features_context,
                model_result_cache=self.model_result_cache
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
                document_features_context=self.document_features_context,
                model_result_cache=self.model_result_cache
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
            if self.use_model:
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
        LOGGER.info('writing training tei to: %r', self.tei_file_path)
        Path(self.tei_file_path).write_bytes(
            etree.tostring(training_tei_root, pretty_print=True)
        )


class FullTextModelTrainingDataGenerator(AbstractModelTrainingDataGenerator):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            training_data_generator=FullTextTeiTrainingDataGenerator()
        )

    def generate_data_for_layout_document(
        self,
        layout_document: LayoutDocument
    ):
        assert self.tei_file_path
        segmentation_model = self.fulltext_models.segmentation_model
        fulltext_model = self.fulltext_models.fulltext_model
        data_generator = fulltext_model.get_data_generator(
            document_features_context=self.document_features_context
        )
        training_data_generator = FullTextTeiTrainingDataGenerator()
        segmentation_label_model_data_list = (
            get_segmentation_label_model_data_list_for_layout_document(
                layout_document,
                segmentation_model=segmentation_model,
                document_features_context=self.document_features_context,
                model_result_cache=self.model_result_cache
            )
        )
        segmentation_label_result = get_layout_document_label_result_for_labeled_model_data_list(
            labeled_model_data_iterable=segmentation_label_model_data_list,
            layout_document=layout_document
        )
        body_layout_document = segmentation_label_result.get_filtered_document_by_label(
            '<body>'
        ).remove_empty_blocks()
        model_data_list: Sequence[LayoutModelData]
        if self.use_model:
            model_data_list = (
                get_fulltext_label_model_data_list_for_layout_document(
                    body_layout_document,
                    fulltext_model=fulltext_model,
                    document_features_context=self.document_features_context,
                    model_result_cache=self.model_result_cache
                )
            )
        else:
            model_data_list = list(
                data_generator.iter_model_data_for_layout_document(body_layout_document)
            )
        training_tei_root = (
            training_data_generator
            .get_training_tei_xml_for_model_data_iterable(
                model_data_list
            )
        )
        LOGGER.info('writing training tei to: %r', self.tei_file_path)
        Path(self.tei_file_path).write_bytes(
            etree.tostring(training_tei_root, pretty_print=True)
        )
        if self.data_file_path:
            LOGGER.info('writing training raw data to: %r', self.data_file_path)
            Path(self.data_file_path).write_text('\n'.join(
                model_data.data_line
                for model_data in model_data_list
            ), encoding='utf-8')


class FigureModelTrainingDataGenerator(AbstractModelTrainingDataGenerator):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            training_data_generator=FigureTeiTrainingDataGenerator()
        )

    def generate_data_for_layout_document(  # pylint: disable=too-many-locals
        self,
        layout_document: LayoutDocument
    ):
        assert self.tei_file_path
        segmentation_model = self.fulltext_models.segmentation_model
        fulltext_model = self.fulltext_models.fulltext_model
        figure_model = self.fulltext_models.figure_model
        data_generator = figure_model.get_data_generator(
            document_features_context=self.document_features_context
        )
        training_data_generator = FigureTeiTrainingDataGenerator()
        segmentation_label_model_data_list = (
            get_segmentation_label_model_data_list_for_layout_document(
                layout_document,
                segmentation_model=segmentation_model,
                document_features_context=self.document_features_context,
                model_result_cache=self.model_result_cache
            )
        )
        segmentation_label_result = get_layout_document_label_result_for_labeled_model_data_list(
            labeled_model_data_iterable=segmentation_label_model_data_list,
            layout_document=layout_document
        )
        body_layout_document = segmentation_label_result.get_filtered_document_by_label(
            '<body>'
        ).remove_empty_blocks()
        fulltext_model_data_list = (
            get_fulltext_label_model_data_list_for_layout_document(
                body_layout_document,
                fulltext_model=fulltext_model,
                document_features_context=self.document_features_context,
                model_result_cache=self.model_result_cache
            )
        )
        fulltext_labeled_layout_tokens = list(
            iter_labeled_layout_token_for_layout_model_label(
                iter_layout_model_label_for_labeled_model_data_list(
                    fulltext_model_data_list
                )
            )
        )
        raw_figure_list = list(
            SemanticMixedContentWrapper(list(
                fulltext_model.iter_semantic_content_for_labeled_layout_tokens(
                    fulltext_labeled_layout_tokens
                )
            )).iter_by_type_recursively(SemanticRawFigure)
        )
        LOGGER.info('raw_figure_list count: %d', len(raw_figure_list))

        model_data_list_list: Sequence[Sequence[LayoutModelData]] = []
        if not raw_figure_list:
            LOGGER.info('no figures found')
            return
        figure_documents = [
            LayoutDocument.for_blocks(
                list(raw_figure.iter_blocks())
            )
            for raw_figure in raw_figure_list
        ]
        model_data_list_list = [
            list(
                data_generator.iter_model_data_for_layout_document(figure_document)
            )
            for figure_document in figure_documents
        ]
        if self.use_model:
            model_data_list_list = get_labeled_model_data_list_list(
                model_data_list_list,
                model=figure_model
            )
        training_tei_root = (
            training_data_generator
            .get_training_tei_xml_for_multiple_model_data_iterables(
                model_data_list_list
            )
        )
        LOGGER.info('writing training tei to: %r', self.tei_file_path)
        Path(self.tei_file_path).write_bytes(
            etree.tostring(training_tei_root, pretty_print=True)
        )
        if self.data_file_path:
            LOGGER.info('writing training raw data to: %r', self.data_file_path)
            Path(self.data_file_path).write_text('\n'.join(
                iter_data_lines_for_model_data_iterables(model_data_list_list)
            ), encoding='utf-8')


class ReferenceSegmenterModelTrainingDataGenerator(AbstractModelTrainingDataGenerator):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            training_data_generator=ReferenceSegmenterTeiTrainingDataGenerator()
        )

    def generate_data_for_layout_document(
        self,
        layout_document: LayoutDocument
    ):
        assert self.tei_file_path
        segmentation_model = self.fulltext_models.segmentation_model
        reference_segmenter_model = self.fulltext_models.reference_segmenter_model
        data_generator = reference_segmenter_model.get_data_generator(
            document_features_context=self.document_features_context
        )
        training_data_generator = ReferenceSegmenterTeiTrainingDataGenerator()
        segmentation_label_model_data_list = (
            get_segmentation_label_model_data_list_for_layout_document(
                layout_document,
                segmentation_model=segmentation_model,
                document_features_context=self.document_features_context,
                model_result_cache=self.model_result_cache
            )
        )
        segmentation_label_result = get_layout_document_label_result_for_labeled_model_data_list(
            labeled_model_data_iterable=segmentation_label_model_data_list,
            layout_document=layout_document
        )
        ref_layout_document = segmentation_label_result.get_filtered_document_by_label(
            '<references>'
        ).remove_empty_blocks()
        model_data_list: Sequence[LayoutModelData]
        if self.use_model:
            model_data_list = (
                get_labeled_model_data_list_for_layout_document(
                    ref_layout_document,
                    model=reference_segmenter_model,
                    document_features_context=self.document_features_context
                )
            )
        else:
            model_data_list = list(
                data_generator.iter_model_data_for_layout_document(ref_layout_document)
            )
        training_tei_root = (
            training_data_generator
            .get_training_tei_xml_for_model_data_iterable(
                model_data_list
            )
        )
        LOGGER.info('writing training tei to: %r', self.tei_file_path)
        Path(self.tei_file_path).write_bytes(
            etree.tostring(training_tei_root, pretty_print=True)
        )
        if self.data_file_path:
            LOGGER.info('writing training raw data to: %r', self.data_file_path)
            Path(self.data_file_path).write_text('\n'.join(
                model_data.data_line
                for model_data in model_data_list
            ), encoding='utf-8')


class CitationModelTrainingDataGenerator(AbstractModelTrainingDataGenerator):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            training_data_generator=CitationTeiTrainingDataGenerator()
        )

    def generate_data_for_layout_document(  # pylint: disable=too-many-locals
        self,
        layout_document: LayoutDocument
    ):
        assert self.tei_file_path
        segmentation_model = self.fulltext_models.segmentation_model
        reference_segmenter_model = self.fulltext_models.reference_segmenter_model
        citation_model = self.fulltext_models.citation_model
        data_generator = citation_model.get_data_generator(
            document_features_context=self.document_features_context
        )
        training_data_generator = CitationTeiTrainingDataGenerator()
        segmentation_label_model_data_list = (
            get_segmentation_label_model_data_list_for_layout_document(
                layout_document,
                segmentation_model=segmentation_model,
                document_features_context=self.document_features_context,
                model_result_cache=self.model_result_cache
            )
        )
        segmentation_label_result = get_layout_document_label_result_for_labeled_model_data_list(
            labeled_model_data_iterable=segmentation_label_model_data_list,
            layout_document=layout_document
        )
        references_layout_document = segmentation_label_result.get_filtered_document_by_label(
            '<references>'
        ).remove_empty_blocks()
        reference_segmenter_model_data_list = (
            get_reference_segmenter_label_model_data_list_for_layout_document(
                references_layout_document,
                reference_segmenter_model=reference_segmenter_model,
                document_features_context=self.document_features_context,
                model_result_cache=self.model_result_cache
            )
        )
        reference_segmenter_labeled_layout_tokens = list(
            iter_labeled_layout_token_for_layout_model_label(
                iter_layout_model_label_for_labeled_model_data_list(
                    reference_segmenter_model_data_list
                )
            )
        )
        raw_reference_text_list = [
            raw_reference_text
            for raw_reference in SemanticMixedContentWrapper(list(
                reference_segmenter_model.iter_semantic_content_for_labeled_layout_tokens(
                    reference_segmenter_labeled_layout_tokens
                )
            )).iter_by_type(SemanticRawReference)
            for raw_reference_text in raw_reference.iter_by_type(SemanticRawReferenceText)
        ]
        LOGGER.info('raw_reference_text_list count: %d', len(raw_reference_text_list))

        model_data_list_list: Sequence[Sequence[LayoutModelData]] = []
        if raw_reference_text_list:
            references_documents = [
                LayoutDocument.for_blocks(
                    list(semantic_raw_reference_text.iter_blocks())
                )
                for semantic_raw_reference_text in raw_reference_text_list
            ]
            model_data_list_list = [
                list(
                    data_generator.iter_model_data_for_layout_document(references_document)
                )
                for references_document in references_documents
            ]
            if self.use_model:
                model_data_list_list = get_labeled_model_data_list_list(
                    model_data_list_list,
                    model=citation_model
                )
        training_tei_root = (
            training_data_generator
            .get_training_tei_xml_for_multiple_model_data_iterables(
                model_data_list_list
            )
        )
        LOGGER.info('writing training tei to: %r', self.tei_file_path)
        Path(self.tei_file_path).write_bytes(
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
    SegmentationModelTrainingDataGenerator(
        output_path=output_path,
        source_filename=source_filename,
        document_features_context=document_features_context,
        fulltext_models=fulltext_models,
        use_model=use_model,
        model_result_cache=model_result_cache
    ).generate_data_for_layout_document(layout_document)
    HeaderModelTrainingDataGenerator(
        output_path=output_path,
        source_filename=source_filename,
        document_features_context=document_features_context,
        fulltext_models=fulltext_models,
        use_model=use_model,
        model_result_cache=model_result_cache
    ).generate_data_for_layout_document(layout_document)
    AffiliationAddressModelTrainingDataGenerator(
        output_path=output_path,
        source_filename=source_filename,
        document_features_context=document_features_context,
        fulltext_models=fulltext_models,
        use_model=use_model,
        model_result_cache=model_result_cache
    ).generate_data_for_layout_document(layout_document)
    FullTextModelTrainingDataGenerator(
        output_path=output_path,
        source_filename=source_filename,
        document_features_context=document_features_context,
        fulltext_models=fulltext_models,
        use_model=use_model,
        model_result_cache=model_result_cache
    ).generate_data_for_layout_document(layout_document)
    FigureModelTrainingDataGenerator(
        output_path=output_path,
        source_filename=source_filename,
        document_features_context=document_features_context,
        fulltext_models=fulltext_models,
        use_model=use_model,
        model_result_cache=model_result_cache
    ).generate_data_for_layout_document(layout_document)
    ReferenceSegmenterModelTrainingDataGenerator(
        output_path=output_path,
        source_filename=source_filename,
        document_features_context=document_features_context,
        fulltext_models=fulltext_models,
        use_model=use_model,
        model_result_cache=model_result_cache
    ).generate_data_for_layout_document(layout_document)
    CitationModelTrainingDataGenerator(
        output_path=output_path,
        source_filename=source_filename,
        document_features_context=document_features_context,
        fulltext_models=fulltext_models,
        use_model=use_model,
        model_result_cache=model_result_cache
    ).generate_data_for_layout_document(layout_document)


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
    if args.debug:
        for name in [__name__, 'sciencebeam_parser', 'sciencebeam_trainer_delft']:
            logging.getLogger(name).setLevel('DEBUG')
    run(args)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()
