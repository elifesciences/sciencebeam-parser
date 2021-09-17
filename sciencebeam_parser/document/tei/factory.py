from abc import ABC, abstractmethod
import logging
from typing import (
    Dict,
    Iterable,
    List,
    Optional,
    Union
)

from lxml import etree

from sciencebeam_parser.document.layout_document import LayoutBlock
from sciencebeam_parser.document.semantic_document import (
    SemanticContentWrapper
)


LOGGER = logging.getLogger(__name__)


T_ElementChildrenListItem = Union[dict, str, etree.ElementBase]
T_ElementChildrenList = List[T_ElementChildrenListItem]


class TeiElementFactoryContext(ABC):
    @abstractmethod
    def get_default_attributes_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        **kwargs
    ) -> Dict[str, str]:
        pass

    @abstractmethod
    def iter_layout_block_tei_children(
        self,
        layout_block: LayoutBlock,
        enable_coordinates: bool = True
    ) -> Iterable[Union[str, etree.ElementBase]]:
        pass

    @abstractmethod
    def get_tei_child_elements_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper
    ) -> List[etree.ElementBase]:
        pass

    @abstractmethod
    def append_tei_children_list_and_get_whitespace(
        self,
        children: T_ElementChildrenList,
        semantic_content: SemanticContentWrapper,
        pending_whitespace: str
    ) -> str:
        pass

    @abstractmethod
    def get_parent_path_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper
    ) -> Optional[List[str]]:
        pass


class TeiElementFactory(ABC):
    @abstractmethod
    def get_tei_children_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> T_ElementChildrenList:
        pass


class SingleElementTeiElementFactory(TeiElementFactory):
    @abstractmethod
    def get_tei_element_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> etree.ElementBase:
        pass

    def get_tei_children_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> T_ElementChildrenList:
        return [self.get_tei_element_for_semantic_content(
            semantic_content, context=context
        )]
