import logging
from typing import Iterable, Optional, Tuple

from pygrobid.document.semantic_document import (
    SemanticAuthor,
    SemanticGivenName,
    SemanticLabel,
    SemanticNote,
    SemanticSurname
)
from pygrobid.document.layout_document import LayoutBlock
from pygrobid.models.name.data import NameDataGenerator
from pygrobid.models.name.extract import NameSemanticExtractor
from pygrobid.models.delft_model import DelftModel


LOGGER = logging.getLogger(__name__)


class NameModel(DelftModel):
    def get_data_generator(self) -> NameDataGenerator:
        return NameDataGenerator()

    def get_semantic_extractor(self) -> NameSemanticExtractor:
        return NameSemanticExtractor()

    def iter_semantic_author_for_entity_blocks(
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]]
    ) -> Iterable[SemanticAuthor]:
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        author: Optional[SemanticAuthor] = None
        for name, layout_block in entity_tokens:
            if not author:
                author = SemanticAuthor()
            if name == '<marker>':
                marker = SemanticLabel(layout_block=layout_block)
                author.add_content(marker)
                yield author
                author = None
                continue
            if name == '<forename>':
                forename = SemanticGivenName()
                forename.add_block_content(layout_block)
                author.add_content(forename)
                continue
            if name == '<surname>':
                surname = SemanticSurname()
                surname.add_block_content(layout_block)
                author.add_content(surname)
                continue
            author.add_content(SemanticNote(
                layout_block=layout_block,
                note_type=name
            ))
        if author:
            yield author
