import logging
from typing import Iterable, Optional, Tuple

from sciencebeam_parser.utils.misc import iter_ids
from sciencebeam_parser.document.semantic_document import (
    SemanticContentWrapper,
    SemanticHeading,
    SemanticLabel,
    SemanticNote,
    SemanticRawReference,
    SemanticRawReferenceText
)
from sciencebeam_parser.document.layout_document import LayoutBlock
from sciencebeam_parser.models.extract import ModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


def is_looks_like_reference(layout_block: LayoutBlock) -> bool:
    # a quick and dirty check whether this remotely looks like a reference
    return len(list(layout_block.iter_all_tokens())) > 3


class ReferenceSegmenterSemanticExtractor(ModelSemanticExtractor):
    def iter_semantic_content_for_entity_blocks(
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        **kwargs
    ) -> Iterable[SemanticContentWrapper]:
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        ids_iterator = iter(iter_ids('b'))
        ref: Optional[SemanticRawReference] = None
        is_first_ref = True
        for name, layout_block in entity_tokens:
            if name == '<label>':
                if not ref:
                    ref = SemanticRawReference(content_id=next(ids_iterator, '?'))
                ref.add_content(SemanticLabel(layout_block=layout_block))
                continue
            if name == '<reference>':
                if not ref and is_first_ref and not is_looks_like_reference(layout_block):
                    yield SemanticHeading(layout_block=layout_block)
                    is_first_ref = False
                    continue
                if not ref:
                    ref = SemanticRawReference(content_id=next(ids_iterator, '?'))
                ref.add_content(SemanticRawReferenceText(layout_block=layout_block))
                yield ref
                ref = None
                is_first_ref = False
                continue
            yield SemanticNote(layout_block=layout_block, note_type=name)
        if ref:
            yield ref
