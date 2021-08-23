import logging
from typing import Iterable, Tuple

from sciencebeam_parser.document.layout_document import (
    LayoutBlock
)
from sciencebeam_parser.document.semantic_document import (
    SemanticSection,
    SemanticSectionTypes
)
from sciencebeam_parser.models.model import Model

from sciencebeam_parser.models.data import (
    DocumentFeaturesContext
)
from sciencebeam_parser.models.fulltext.data import FullTextDataGenerator
from sciencebeam_parser.models.fulltext.extract import FullTextSemanticExtractor


LOGGER = logging.getLogger(__name__)


class FullTextModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext
    ) -> FullTextDataGenerator:
        return FullTextDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> FullTextSemanticExtractor:
        return FullTextSemanticExtractor()

    def update_section_with_entity_blocks(
        self,
        parent_section: SemanticSection,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        section_type: str = SemanticSectionTypes.OTHER
    ):
        semantic_extractor = self.get_semantic_extractor()
        for semantic_content in semantic_extractor.iter_semantic_content_for_entity_blocks(
            entity_tokens=entity_tokens,
            section_type=section_type
        ):
            parent_section.add_content(semantic_content)

    def get_section_for_entity_blocks(
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]]
    ) -> SemanticSection:
        parent_section = SemanticSection()
        self.update_section_with_entity_blocks(parent_section, entity_tokens)
        return parent_section
