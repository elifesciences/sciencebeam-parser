from abc import ABC, abstractmethod
from typing import Iterable, Mapping, Optional, Tuple

from pygrobid.document.semantic_document import (
    SemanticContentFactoryProtocol,
    SemanticContentWrapper,
    SemanticNote
)
from pygrobid.document.layout_document import LayoutBlock


class ModelSemanticExtractor(ABC):
    @abstractmethod
    def iter_semantic_content_for_entity_blocks(
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        **kwargs
    ) -> Iterable[SemanticContentWrapper]:
        pass


class SimpleModelSemanticExtractor(ModelSemanticExtractor):
    def __init__(
        self,
        semantic_content_class_by_tag: Optional[
            Mapping[str, SemanticContentFactoryProtocol]
        ] = None
    ):
        super().__init__()
        self.semantic_content_class_by_tag = semantic_content_class_by_tag or {}

    def get_semantic_content_for_entity_name(
        self,
        name: str,
        layout_block: LayoutBlock
    ) -> SemanticContentWrapper:
        semantic_content_class = self.semantic_content_class_by_tag.get(name)
        if semantic_content_class:
            return semantic_content_class(layout_block=layout_block)
        return SemanticNote(
            layout_block=layout_block,
            note_type=name
        )
