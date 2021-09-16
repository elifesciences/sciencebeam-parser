import logging

from lxml import etree

from sciencebeam_parser.document.semantic_document import (
    SemanticCaption,
    SemanticContentWrapper,
    SemanticFigure,
    SemanticLabel,
    SemanticTable
)
from sciencebeam_parser.document.tei.common import (
    TEI_E
)
from sciencebeam_parser.document.tei.factory import (
    SingleElementTeiElementFactory,
    TeiElementFactoryContext
)


LOGGER = logging.getLogger(__name__)


class FigureTeiElementFactory(SingleElementTeiElementFactory):
    def get_tei_element_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> etree.ElementBase:
        LOGGER.debug('semantic_content: %s', semantic_content)
        assert isinstance(semantic_content, SemanticFigure)
        semantic_figure = semantic_content
        children = [context.get_default_attributes_for_semantic_content(semantic_figure)]
        for child_semantic_content in semantic_figure:
            if isinstance(child_semantic_content, SemanticLabel):
                layout_block = child_semantic_content.merged_block
                children.append(TEI_E(
                    'head', *context.iter_layout_block_tei_children(layout_block)
                ))
                children.append(TEI_E(
                    'label', *context.iter_layout_block_tei_children(layout_block)
                ))
                continue
            if isinstance(child_semantic_content, SemanticCaption):
                children.append(TEI_E(
                    'figDesc', *context.iter_layout_block_tei_children(
                        child_semantic_content.merged_block
                    )
                ))
                continue
            children.extend(context.get_tei_child_elements_for_semantic_content(
                child_semantic_content
            ))
        return TEI_E('figure', *children)


class TableTeiElementFactory(SingleElementTeiElementFactory):
    def get_tei_element_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> etree.ElementBase:
        LOGGER.debug('semantic_content: %s', semantic_content)
        assert isinstance(semantic_content, SemanticTable)
        semantic_table = semantic_content
        children = [context.get_default_attributes_for_semantic_content(semantic_table)]
        for child_semantic_content in semantic_table:
            if isinstance(child_semantic_content, SemanticLabel):
                layout_block = child_semantic_content.merged_block
                children.append(TEI_E(
                    'head', *context.iter_layout_block_tei_children(layout_block)
                ))
                children.append(TEI_E(
                    'label', *context.iter_layout_block_tei_children(layout_block)
                ))
                continue
            if isinstance(child_semantic_content, SemanticCaption):
                children.append(TEI_E(
                    'figDesc', *context.iter_layout_block_tei_children(
                        child_semantic_content.merged_block
                    )
                ))
                continue
            children.extend(
                context.get_tei_child_elements_for_semantic_content(child_semantic_content)
            )
        return TEI_E('figure', {'type': 'table'}, *children)
