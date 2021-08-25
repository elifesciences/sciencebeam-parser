import logging
import re
from typing import Iterable, Mapping, Optional, Tuple

from sciencebeam_parser.document.semantic_document import (
    SemanticContentFactoryProtocol,
    SemanticContentWrapper,
    SemanticRawAddress,
    SemanticRawAffiliation,
    SemanticRawAffiliationAddress,
    SemanticTitle,
    SemanticAbstract,
    SemanticRawAuthors
)
from sciencebeam_parser.document.layout_document import LayoutBlock, LayoutTokensText
from sciencebeam_parser.models.extract import SimpleModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


# based on:
#   grobid-core/src/main/java/org/grobid/core/data/BiblioItem.java
ABSTRACT_REGEX = r'^(?:(?:abstract|summary|résumé|abrégé|a b s t r a c t)(?:[.:])?)?\s*(.*)'


SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG: Mapping[str, SemanticContentFactoryProtocol] = {
    '<author>': SemanticRawAuthors,
    '<affiliation>': SemanticRawAffiliation,
    '<address>': SemanticRawAddress
}


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


class HeaderSemanticExtractor(SimpleModelSemanticExtractor):
    def __init__(self):
        super().__init__(semantic_content_class_by_tag=SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG)

    def iter_semantic_content_for_entity_blocks(
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        **kwargs
    ) -> Iterable[SemanticContentWrapper]:
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        has_title: bool = False
        has_abstract: bool = False
        aff_address: Optional[SemanticRawAffiliationAddress] = None
        next_previous_label: str = ''
        for name, layout_block in entity_tokens:
            previous_label = next_previous_label
            next_previous_label = name
            if name == '<title>' and not has_title:
                yield SemanticTitle(layout_block=layout_block)
                has_title = True
                continue
            if name == '<abstract>' and not has_abstract:
                abstract_layout_block = get_cleaned_abstract_layout_block(
                    layout_block
                )
                yield SemanticAbstract(layout_block=abstract_layout_block)
                has_abstract = True
                continue
            if name in {'<affiliation>', '<address>'}:
                if (
                    aff_address is not None
                    and name == '<affiliation>'
                    and previous_label in {'<affiliation>', '<address>'}
                ):
                    yield aff_address
                    aff_address = None
                if aff_address is None:
                    aff_address = SemanticRawAffiliationAddress()
                aff_address.add_content(self.get_semantic_content_for_entity_name(
                    name, layout_block
                ))
                continue
            if aff_address is not None:
                yield aff_address
                aff_address = None
            yield self.get_semantic_content_for_entity_name(
                name, layout_block
            )
        if aff_address is not None:
            yield aff_address
