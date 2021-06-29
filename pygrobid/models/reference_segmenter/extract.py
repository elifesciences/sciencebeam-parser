import logging
from typing import Iterable, Optional, Tuple

from pygrobid.utils.misc import iter_ids
from pygrobid.document.semantic_document import (
    SemanticContentWrapper,
    SemanticLabel,
    SemanticNote,
    SemanticRawReference,
    SemanticRawReferenceText
)
from pygrobid.document.layout_document import LayoutBlock
from pygrobid.models.extract import ModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


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
        for name, layout_block in entity_tokens:
            if name == '<label>':
                if not ref:
                    ref = SemanticRawReference()
                    ref.reference_id = next(ids_iterator, '?')
                ref.add_content(SemanticLabel(layout_block=layout_block))
                continue
            if name == '<reference>':
                if not ref:
                    ref = SemanticRawReference()
                    ref.reference_id = next(ids_iterator, '?')
                ref.add_content(SemanticRawReferenceText(layout_block=layout_block))
                yield ref
                ref = None
                continue
            yield SemanticNote(layout_block=layout_block, note_type=name)
        if ref:
            yield ref
