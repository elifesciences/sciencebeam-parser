import logging
import re
from typing import Iterable, Tuple

from pygrobid.document.layout_document import (
    LayoutBlock,
    LayoutTokensText
)
from pygrobid.document.tei_document import TeiDocument
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

    def update_document_with_entity_values(
        self,
        document: TeiDocument,
        entity_values: Iterable[Tuple[str, str]]
    ):
        entity_values = list(entity_values)
        LOGGER.info('entity_values: %s', entity_values)
        current_title = None
        current_abstract = None
        for name, value in entity_values:
            if name == '<title>' and not current_title:
                current_title = value
                document.set_title(value)
            if name == '<abstract>' and not current_abstract:
                value = get_cleaned_abstract_text(value)
                current_abstract = value
                document.set_abstract(value)

    def update_document_with_entity_blocks(
        self,
        document: TeiDocument,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]]
    ):
        entity_tokens = list(entity_tokens)
        LOGGER.info('entity_tokens: %s', entity_tokens)
        current_title_layout_block = None
        current_abstract_layout_block = None
        for name, layout_block in entity_tokens:
            if name == '<title>' and not current_title_layout_block:
                current_title_layout_block = layout_block
                document.set_title_layout_block(layout_block)
            if name == '<abstract>' and not current_abstract_layout_block:
                current_abstract_layout_block = get_cleaned_abstract_layout_block(
                    layout_block
                )
                document.set_abstract_layout_block(current_abstract_layout_block)
