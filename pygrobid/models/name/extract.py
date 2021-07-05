import logging
from typing import Iterable, List, Optional, Tuple, Type, cast

from pygrobid.document.semantic_document import (
    SemanticAuthor,
    SemanticContentWrapper,
    SemanticMarker,
    SemanticMiddleName,
    SemanticNameSuffix,
    SemanticNameTitle,
    SemanticNote,
    SemanticGivenName,
    SemanticSurname,
    T_SemanticName
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

    def iter_semantic_content_for_entity_blocks(  # type: ignore  # pylint: disable=arguments-differ
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        name_type: Optional[Type[T_SemanticName]] = None,
        **kwargs
    ) -> Iterable[T_SemanticName]:
        _name_type: Type[T_SemanticName] = cast(
            Type[T_SemanticName],
            name_type if name_type is not None else SemanticAuthor
        )
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        semantic_name: Optional[T_SemanticName] = None
        seen_entity_tokens: List[Tuple[str, LayoutBlock]] = []
        seen_name_labels: List[str] = []
        has_tail_marker: bool = False
        for name, layout_block in entity_tokens:
            seen_entity_tokens.append((name, layout_block,))
            if name == '<marker>':
                if not semantic_name:
                    LOGGER.debug('new semantic_name with marker in the beginning')
                    semantic_name = _name_type()
                    semantic_name.add_content(SemanticMarker(layout_block=layout_block))
                    continue
                if len(seen_entity_tokens) >= 2 and seen_name_labels and not has_tail_marker:
                    previous_layout_block = seen_entity_tokens[-2][1]
                    if previous_layout_block.text.strip().endswith(','):
                        LOGGER.debug(
                            'new semantic_name marker after comma, seen_name_labels=%s',
                            seen_name_labels
                        )
                        yield semantic_name
                        seen_name_labels = []
                        semantic_name = _name_type()
                        semantic_name.add_content(SemanticMarker(layout_block=layout_block))
                        continue
                semantic_name.add_content(SemanticMarker(layout_block=layout_block))
                has_tail_marker = True
                continue
            semantic_content = self.get_semantic_content_for_entity_name(
                name, layout_block
            )
            if semantic_name and name in SPLIT_ON_SECOND_ENTIY_NAME and name in seen_name_labels:
                LOGGER.debug(
                    'starting new semantic_name after having seen name part again, name=%r',
                    name
                )
                yield semantic_name
                seen_name_labels = []
                has_tail_marker = False
                semantic_name = None
            if not isinstance(semantic_content, SemanticNote):
                if has_tail_marker and semantic_name:
                    LOGGER.debug('starting new semantic_name after tail markers, name=%r', name)
                    yield semantic_name
                    seen_name_labels = []
                    has_tail_marker = False
                    semantic_name = None
                seen_name_labels.append(name)
            if not semantic_name:
                semantic_name = _name_type()
            semantic_name.add_content(semantic_content)
        if semantic_name:
            yield semantic_name
