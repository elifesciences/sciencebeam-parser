import logging
from typing import (
    Iterable,
    List,
)

from lxml import etree

from sciencebeam_parser.document.semantic_document import (
    SemanticContentWrapper,
    SemanticFigure,
    SemanticHeading,
    SemanticLabel,
    SemanticParagraph,
    SemanticRawEquation,
    SemanticSection,
    SemanticSectionTypes,
    SemanticTable
)
from sciencebeam_parser.document.tei.common import (
    TEI_E,
    TeiElementBuilder
)
from sciencebeam_parser.document.tei.factory import (
    SingleElementTeiElementFactory,
    T_ElementChildrenList,
    TeiElementFactory,
    TeiElementFactoryContext
)


LOGGER = logging.getLogger(__name__)


class HeadingTeiElementFactory(SingleElementTeiElementFactory):
    def get_tei_element_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> etree.ElementBase:
        LOGGER.debug('semantic_content: %s', semantic_content)
        assert isinstance(semantic_content, SemanticHeading)
        semantic_heading = semantic_content
        children: T_ElementChildrenList = [
            context.get_default_attributes_for_semantic_content(semantic_heading)
        ]
        pending_whitespace = ''
        for child_semantic_content in semantic_heading:
            if isinstance(child_semantic_content, SemanticLabel):
                children.append({'n': child_semantic_content.get_text()})
                continue
            layout_block = child_semantic_content.merged_block
            if pending_whitespace:
                children.append(pending_whitespace)
            children.extend(context.iter_layout_block_tei_children(
                layout_block=layout_block,
                enable_coordinates=False
            ))
            pending_whitespace = layout_block.whitespace
        return TEI_E('head', *children)


def iter_flat_paragraph_formula(
    semantic_paragraph: SemanticParagraph
) -> Iterable[SemanticContentWrapper]:
    pending_semantic_content_list: List[SemanticContentWrapper] = []
    for semantic_content in semantic_paragraph:
        if isinstance(semantic_content, SemanticRawEquation):
            if pending_semantic_content_list:
                yield SemanticParagraph(pending_semantic_content_list)
                pending_semantic_content_list = []
            yield semantic_content
            continue
        pending_semantic_content_list.append(semantic_content)
    if pending_semantic_content_list:
        yield SemanticParagraph(pending_semantic_content_list)


class ParagraphTeiElementFactory(TeiElementFactory):
    def get_tei_children_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> List[etree.ElementBase]:
        LOGGER.debug('semantic_content: %s', semantic_content)
        assert isinstance(semantic_content, SemanticParagraph)
        semantic_paragraph = semantic_content
        result: List[etree.ElementBase] = []
        for flat_parent_semantic_content in iter_flat_paragraph_formula(semantic_paragraph):
            if not isinstance(flat_parent_semantic_content, SemanticParagraph):
                result.extend(context.get_tei_child_elements_for_semantic_content(
                    flat_parent_semantic_content
                ))
                continue
            children: T_ElementChildrenList = [
                context.get_default_attributes_for_semantic_content(flat_parent_semantic_content)
            ]
            pending_whitespace = ''
            for child_semantic_content in flat_parent_semantic_content:
                pending_whitespace = context.append_tei_children_list_and_get_whitespace(
                    children,
                    child_semantic_content,
                    pending_whitespace=pending_whitespace
                )
            result.append(TEI_E('p', *children))
        return result


class SectionTeiElementFactory(TeiElementFactory):
    def get_tei_children_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> List[etree.ElementBase]:
        LOGGER.debug('semantic_content: %s', semantic_content)
        assert isinstance(semantic_content, SemanticSection)
        semantic_section = semantic_content
        tei_section = TeiElementBuilder(TEI_E('div'))
        for child_semantic_content in semantic_section:
            if isinstance(child_semantic_content, (SemanticFigure, SemanticTable,)):
                # rendered at parent level
                continue
            tei_section.extend(context.get_tei_child_elements_for_semantic_content(
                child_semantic_content
            ))
        if semantic_content.section_type == SemanticSectionTypes.ACKNOWLEDGEMENT:
            tei_section.element.attrib['type'] = 'acknowledgement'
        if not list(tei_section.element):
            return []
        return [tei_section.element]
