import logging
from typing import Iterable, Mapping, Optional, Tuple

from pygrobid.document.semantic_document import (
    SemanticCaption,
    SemanticContentFactoryProtocol,
    SemanticContentWrapper,
    SemanticFigure,
    SemanticLabel,
    SemanticNote
)
from pygrobid.document.layout_document import LayoutBlock
from pygrobid.models.extract import ModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG: Mapping[str, SemanticContentFactoryProtocol] = {
    '<label>': SemanticLabel,
    '<figDesc>': SemanticCaption
}


class FigureSemanticExtractor(ModelSemanticExtractor):
    def get_semantic_content_for_entity_name(  # pylint: disable=too-many-return-statements
        self,
        name: str,
        layout_block: LayoutBlock
    ) -> SemanticContentWrapper:
        semantic_content_class = SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG.get(name)
        if semantic_content_class:
            return semantic_content_class(layout_block=layout_block)
        return SemanticNote(
            layout_block=layout_block,
            note_type=name
        )

    def iter_semantic_content_for_entity_blocks(  # pylint: disable=arguments-differ
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        **kwargs
    ) -> Iterable[SemanticContentWrapper]:
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        figure: Optional[SemanticFigure] = None
        for name, layout_block in entity_tokens:
            if not figure:
                figure = SemanticFigure()
            semantic_content = self.get_semantic_content_for_entity_name(
                name, layout_block=layout_block
            )
            figure.add_content(semantic_content)
        if figure:
            yield figure
