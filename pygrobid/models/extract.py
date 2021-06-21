from abc import ABC, abstractmethod
from typing import Iterable, Tuple

from pygrobid.document.semantic_document import SemanticContentWrapper
from pygrobid.document.layout_document import LayoutBlock


class ModelSemanticExtractor(ABC):
    @abstractmethod
    def iter_semantic_content_for_entity_blocks(
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]]
    ) -> Iterable[SemanticContentWrapper]:
        pass
