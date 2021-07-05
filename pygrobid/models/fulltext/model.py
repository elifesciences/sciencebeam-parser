import logging
from typing import Iterable, Tuple

from pygrobid.document.layout_document import (
    LayoutBlock
)
from pygrobid.document.semantic_document import (
    SemanticSection,
    SemanticSectionTypes
)
from pygrobid.models.model import Model

from pygrobid.models.fulltext.data import FullTextDataGenerator
from pygrobid.models.fulltext.extract import FullTextSemanticExtractor


LOGGER = logging.getLogger(__name__)


class FullTextModel(Model):
    def get_data_generator(self) -> FullTextDataGenerator:
        return FullTextDataGenerator()

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
