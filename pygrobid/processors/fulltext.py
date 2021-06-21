import logging

from dataclasses import dataclass
from typing import List
from pygrobid.config.config import AppConfig
from pygrobid.models.model import LayoutDocumentLabelResult

from pygrobid.document.semantic_document import (
    SemanticContentWrapper,
    SemanticDocument,
    SemanticRawAuthors,
    SemanticSection,
    SemanticSectionTypes
)
from pygrobid.document.tei_document import TeiDocument, get_tei_for_semantic_document
from pygrobid.document.layout_document import LayoutDocument
from pygrobid.models.segmentation.model import SegmentationModel
from pygrobid.models.header.model import HeaderModel
from pygrobid.models.name.model import NameModel
from pygrobid.models.fulltext.model import FullTextModel


LOGGER = logging.getLogger(__name__)


@dataclass
class FullTextModels:
    segmentation_model: SegmentationModel
    header_model: HeaderModel
    name_header_model: NameModel
    fulltext_model: FullTextModel


def load_models(app_config: AppConfig) -> FullTextModels:
    models_config = app_config['models']
    segmentation_model = SegmentationModel(models_config['segmentation']['path'])
    header_model = HeaderModel(models_config['header']['path'])
    name_header_model = NameModel(models_config['name-header']['path'])
    fulltext_model = FullTextModel(models_config['fulltext']['path'])
    return FullTextModels(
        segmentation_model=segmentation_model,
        header_model=header_model,
        name_header_model=name_header_model,
        fulltext_model=fulltext_model
    )


class FullTextProcessor:
    def __init__(
        self,
        fulltext_models: FullTextModels
    ) -> None:
        self.fulltext_models = fulltext_models

    @property
    def segmentation_model(self) -> SegmentationModel:
        return self.fulltext_models.segmentation_model

    @property
    def header_model(self) -> HeaderModel:
        return self.fulltext_models.header_model

    @property
    def name_header_model(self) -> NameModel:
        return self.fulltext_models.name_header_model

    @property
    def fulltext_model(self) -> FullTextModel:
        return self.fulltext_models.fulltext_model

    def get_semantic_document_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> SemanticDocument:
        segmentation_label_result = self.segmentation_model.get_label_layout_document_result(
            layout_document
        )
        header_layout_document = segmentation_label_result.get_filtered_document_by_label(
            '<header>'
        ).remove_empty_blocks()
        LOGGER.debug('header_layout_document: %s', header_layout_document)
        document = SemanticDocument()
        if header_layout_document.pages:
            labeled_layout_tokens = self.header_model.predict_labels_for_layout_document(
                header_layout_document
            )
            LOGGER.debug('labeled_layout_tokens: %r', labeled_layout_tokens)
            entity_blocks = self.header_model.iter_entity_layout_blocks_for_labeled_layout_tokens(
                labeled_layout_tokens
            )
            self.header_model.update_semantic_document_with_entity_blocks(
                document, entity_blocks
            )
            self._process_raw_authors(document)

        self._update_semantic_section_using_segmentation_result_and_fulltext_model(
            document.body_section,
            segmentation_label_result,
            '<body>',
            SemanticSectionTypes.OTHER
        )
        self._update_semantic_section_using_segmentation_result_and_fulltext_model(
            document.back_section,
            segmentation_label_result,
            '<acknowledgement>',
            SemanticSectionTypes.ACKNOWLEDGEMENT
        )
        self._update_semantic_section_using_segmentation_result_and_fulltext_model(
            document.back_section,
            segmentation_label_result,
            '<annex>',
            SemanticSectionTypes.OTHER
        )
        return document

    def _process_raw_authors(self, semantic_document: SemanticDocument):
        result_content: List[SemanticContentWrapper] = []
        raw_authors: List[SemanticRawAuthors] = []
        for semantic_content in semantic_document.front:
            if isinstance(semantic_content, SemanticRawAuthors):
                raw_authors.append(semantic_content)
                continue
            result_content.append(semantic_content)
        if raw_authors:
            raw_authors_layout_document = LayoutDocument.for_blocks([
                block
                for raw_author in raw_authors
                for block in raw_author.iter_blocks()
            ])
            labeled_layout_tokens = self.name_header_model.predict_labels_for_layout_document(
                raw_authors_layout_document
            )
            LOGGER.debug('labeled_layout_tokens (author): %r', labeled_layout_tokens)
            authors_iterable = (
                self.name_header_model.iter_semantic_content_for_labeled_layout_tokens(
                    labeled_layout_tokens
                )
            )
            for author in authors_iterable:
                result_content.append(author)
        semantic_document.front.mixed_content = result_content

    def _update_semantic_section_using_segmentation_result_and_fulltext_model(
        self,
        semantic_section: SemanticSection,
        segmentation_label_result: LayoutDocumentLabelResult,
        segmentation_tag: str,
        section_type: str
    ):
        layout_document = segmentation_label_result.get_filtered_document_by_label(
            segmentation_tag
        ).remove_empty_blocks()
        self._update_semantic_section_using_layout_document_and_fulltext_model(
            semantic_section,
            layout_document,
            section_name=segmentation_tag,
            section_type=section_type
        )

    def _update_semantic_section_using_layout_document_and_fulltext_model(
        self,
        semantic_section: SemanticSection,
        layout_document: LayoutDocument,
        section_name: str,
        section_type: str
    ):
        LOGGER.debug('layout_document (%r): %s', section_name, layout_document)
        if not layout_document.pages:
            return
        labeled_layout_tokens = self.fulltext_model.predict_labels_for_layout_document(
            layout_document
        )
        LOGGER.debug('labeled_layout_tokens (%r): %r', section_name, labeled_layout_tokens)
        entity_blocks = self.fulltext_model.iter_entity_layout_blocks_for_labeled_layout_tokens(
            labeled_layout_tokens
        )
        self.fulltext_model.update_section_with_entity_blocks(
            semantic_section,
            entity_blocks,
            section_type=section_type
        )

    def get_tei_document_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> TeiDocument:
        return get_tei_for_semantic_document(
            self.get_semantic_document_for_layout_document(
                layout_document
            )
        )
