import logging
from typing import Iterable, Tuple

from pygrobid.document.layout_document import LayoutBlock
from pygrobid.document.semantic_document import SemanticDocument
from pygrobid.models.header.data import HeaderDataGenerator
from pygrobid.models.header.extract import HeaderSemanticExtractor
from pygrobid.models.delft_model import DelftModel


LOGGER = logging.getLogger(__name__)


class HeaderModel(DelftModel):
    def get_data_generator(self) -> HeaderDataGenerator:
        return HeaderDataGenerator()

    def get_semantic_extractor(self) -> HeaderSemanticExtractor:
        return HeaderSemanticExtractor()

    def update_semantic_document_with_entity_blocks(
        self,
        document: SemanticDocument,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]]
    ):
        semantic_content_iterable = (
            self.get_semantic_extractor()
            .iter_semantic_content_for_entity_blocks(entity_tokens)
        )
        front = document.front
        for semantic_content in semantic_content_iterable:
            front.add_content(semantic_content)
