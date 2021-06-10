import logging

from dataclasses import dataclass

from pygrobid.document.semantic_document import SemanticDocument
from pygrobid.document.tei_document import TeiDocument, get_tei_for_semantic_document
from pygrobid.document.layout_document import LayoutDocument
from pygrobid.models.segmentation.model import SegmentationModel
from pygrobid.models.header.model import HeaderModel
from pygrobid.models.fulltext.model import FullTextModel


LOGGER = logging.getLogger(__name__)


@dataclass
class FullTextModels:
    segmentation_model: SegmentationModel
    header_model: HeaderModel
    fulltext_model: FullTextModel


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

        body_layout_document = segmentation_label_result.get_filtered_document_by_label(
            '<body>'
        ).remove_empty_blocks()
        LOGGER.debug('body_layout_document: %s', body_layout_document)
        if body_layout_document.pages:
            labeled_layout_tokens = self.fulltext_model.predict_labels_for_layout_document(
                body_layout_document
            )
            LOGGER.debug('labeled_layout_tokens: %r', labeled_layout_tokens)
            entity_blocks = self.fulltext_model.iter_entity_layout_blocks_for_labeled_layout_tokens(
                labeled_layout_tokens
            )
            self.fulltext_model.update_section_with_entity_blocks(
                document.body_section,
                entity_blocks
            )

        return document

    def get_tei_document_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> TeiDocument:
        return get_tei_for_semantic_document(
            self.get_semantic_document_for_layout_document(
                layout_document
            )
        )
