import logging
from typing import Iterable, Optional, Tuple

from pygrobid.utils.misc import iter_ids
from pygrobid.document.semantic_document import (
    SemanticContentWrapper,
    SemanticNote,
    SemanticRawAuthors,
    SemanticRawReference,
    SemanticReference,
    SemanticTitle
)
from pygrobid.document.layout_document import LayoutBlock
from pygrobid.models.extract import ModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


class CitationSemanticExtractor(ModelSemanticExtractor):
    def get_semantic_content_for_entity_name(  # pylint: disable=too-many-return-statements
        self,
        name: str,
        layout_block: LayoutBlock
    ) -> SemanticContentWrapper:
        if name == '<author>':
            return SemanticRawAuthors(layout_block=layout_block)
        if name == '<title>':
            return SemanticTitle(layout_block=layout_block)
        return SemanticNote(
            layout_block=layout_block,
            note_type=name
        )

    def iter_semantic_content_for_entity_blocks(  # pylint: disable=arguments-differ
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        semantic_raw_reference: Optional[SemanticRawReference] = None,
        **kwargs
    ) -> Iterable[SemanticContentWrapper]:
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        ids_iterator = iter(iter_ids('b'))
        ref: Optional[SemanticReference] = None
        for name, layout_block in entity_tokens:
            if not ref:
                ref = SemanticReference()
                if semantic_raw_reference:
                    ref.reference_id = semantic_raw_reference.reference_id
                    for semantic_content in semantic_raw_reference:
                        ref.add_content(semantic_content)
                if not ref.reference_id:
                    ref.reference_id = next(ids_iterator, '?')
            semantic_content = self.get_semantic_content_for_entity_name(
                name, layout_block=layout_block
            )
            ref.add_content(semantic_content)
        if ref:
            yield ref
