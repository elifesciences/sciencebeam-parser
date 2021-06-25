import logging
from typing import Iterable, List, Optional, Tuple

from pygrobid.document.semantic_document import (
    SemanticAuthor,
    SemanticContentWrapper,
    SemanticMarker,
    SemanticMiddleName,
    SemanticNameSuffix,
    SemanticNameTitle,
    SemanticNote,
    SemanticGivenName,
    SemanticSurname
)
from pygrobid.document.layout_document import LayoutBlock
from pygrobid.models.extract import ModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


SPLIT_ON_SECOND_ENTIY_NAME = {'<title>', '<forename>', '<surname>'}


class NameSemanticExtractor(ModelSemanticExtractor):
    def get_semantic_content_for_entity_name(
        self,
        name: str,
        layout_block: LayoutBlock
    ) -> SemanticContentWrapper:
        if name == '<title>':
            return SemanticNameTitle(layout_block=layout_block)
        if name == '<forename>':
            return SemanticGivenName(layout_block=layout_block)
        if name == '<middlename>':
            return SemanticMiddleName(layout_block=layout_block)
        if name == '<surname>':
            return SemanticSurname(layout_block=layout_block)
        if name == '<suffix>':
            return SemanticNameSuffix(layout_block=layout_block)
        return SemanticNote(
            layout_block=layout_block,
            note_type=name
        )

    def iter_semantic_content_for_entity_blocks(
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        **kwargs
    ) -> Iterable[SemanticAuthor]:
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        author: Optional[SemanticAuthor] = None
        seen_entity_tokens: List[Tuple[str, LayoutBlock]] = []
        seen_author_labels: List[str] = []
        has_tail_marker: bool = False
        for name, layout_block in entity_tokens:
            seen_entity_tokens.append((name, layout_block,))
            if name == '<marker>':
                if not author:
                    LOGGER.debug('new author with marker in the beginning')
                    author = SemanticAuthor()
                    author.add_content(SemanticMarker(layout_block=layout_block))
                    continue
                if len(seen_entity_tokens) >= 2 and seen_author_labels and not has_tail_marker:
                    previous_layout_block = seen_entity_tokens[-2][1]
                    if previous_layout_block.text.strip().endswith(','):
                        LOGGER.debug(
                            'new author marker after comma, seen_author_labels=%s',
                            seen_author_labels
                        )
                        yield author
                        seen_author_labels = []
                        author = SemanticAuthor()
                        author.add_content(SemanticMarker(layout_block=layout_block))
                        continue
                author.add_content(SemanticMarker(layout_block=layout_block))
                has_tail_marker = True
                continue
            semantic_content = self.get_semantic_content_for_entity_name(
                name, layout_block
            )
            if author and name in SPLIT_ON_SECOND_ENTIY_NAME and name in seen_author_labels:
                LOGGER.debug(
                    'starting new author after having seen name part again, name=%r',
                    name
                )
                yield author
                seen_author_labels = []
                has_tail_marker = False
                author = None
            if not isinstance(semantic_content, SemanticNote):
                if has_tail_marker and author:
                    LOGGER.debug('starting new author after tail markers, name=%r', name)
                    yield author
                    seen_author_labels = []
                    has_tail_marker = False
                    author = None
                seen_author_labels.append(name)
            if not author:
                author = SemanticAuthor()
            author.add_content(semantic_content)
        if author:
            yield author
