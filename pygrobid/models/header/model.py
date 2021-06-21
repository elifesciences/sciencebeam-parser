import logging
import re
from typing import Iterable, Tuple

from pygrobid.document.layout_document import (
    LayoutBlock,
    LayoutTokensText
)
from pygrobid.document.semantic_document import SemanticDocument, SemanticRawAuthors
from pygrobid.models.header.data import HeaderDataGenerator
from pygrobid.models.delft_model import DelftModel


LOGGER = logging.getLogger(__name__)


# based on:
#   grobid-core/src/main/java/org/grobid/core/data/BiblioItem.java
ABSTRACT_REGEX = r'^(?:(?:abstract|summary|résumé|abrégé|a b s t r a c t)(?:[.:])?)?\s*(.*)'


def get_cleaned_abstract_text(text: str) -> str:
    if not text:
        return text
    m = re.match(ABSTRACT_REGEX, text, re.IGNORECASE)
    if not m:
        LOGGER.debug('text does not match regex: %r', text)
        return text
    return m.group(1)


def get_cleaned_abstract_layout_block(layout_block: LayoutBlock) -> LayoutBlock:
    if not layout_block or not layout_block.lines:
        return layout_block
    layout_tokens_text = LayoutTokensText(layout_block)
    text = str(layout_tokens_text)
    m = re.match(ABSTRACT_REGEX, text, re.IGNORECASE)
    if not m:
        LOGGER.debug('text does not match regex: %r', text)
        return layout_block
    start = m.start(1)
    LOGGER.debug('start: %d (text: %r)', start, text)
    return LayoutBlock.for_tokens(list(
        layout_tokens_text.iter_layout_tokens_between(start, len(text))
    ))


class HeaderModel(DelftModel):
    def get_data_generator(self) -> HeaderDataGenerator:
        return HeaderDataGenerator()

    def update_semantic_document_with_entity_blocks(
        self,
        document: SemanticDocument,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]]
    ):
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        for name, layout_block in entity_tokens:
            if name == '<title>' and not document.meta.title:
                document.meta.title.add_block_content(layout_block)
            if name == '<abstract>' and not document.meta.abstract:
                abstract_layout_block = get_cleaned_abstract_layout_block(
                    layout_block
                )
                document.meta.abstract.add_block_content(abstract_layout_block)
            if name == '<author>':
                author = SemanticRawAuthors()
                author.add_block_content(layout_block)
                document.front.add_content(author)
