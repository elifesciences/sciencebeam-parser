import logging
from typing import (
    List
)

from lxml import etree

from sciencebeam_parser.document.semantic_document import (
    SemanticContentWrapper,
    SemanticRawEquation,
    SemanticRawEquationContent
)
from sciencebeam_parser.document.tei.common import (
    TEI_E
)
from sciencebeam_parser.document.tei.factory import (
    T_ElementChildrenList,
    TeiElementFactory,
    TeiElementFactoryContext
)


LOGGER = logging.getLogger(__name__)


class RawEquationTeiElementFactory(TeiElementFactory):
    def get_tei_children_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> List[etree.ElementBase]:
        LOGGER.debug('semantic_content: %s', semantic_content)
        assert isinstance(semantic_content, SemanticRawEquation)
        semantic_raw_equation = semantic_content
        children: T_ElementChildrenList = [
            context.get_default_attributes_for_semantic_content(semantic_raw_equation)
        ]
        pending_whitespace = ''
        for child_semantic_content in semantic_raw_equation:
            if isinstance(child_semantic_content, SemanticRawEquationContent):
                layout_block = child_semantic_content.merged_block
                if pending_whitespace:
                    children.append(pending_whitespace)
                children.extend(context.iter_layout_block_tei_children(layout_block))
                pending_whitespace = layout_block.whitespace
                continue
            pending_whitespace = context.append_tei_children_list_and_get_whitespace(
                children,
                child_semantic_content,
                pending_whitespace=pending_whitespace
            )
        return [TEI_E('formula', *children)]
