import logging
import re
from typing import Iterable, Dict, List, Optional, Union

from lxml import etree
from lxml.builder import ElementMaker

from pygrobid.document.layout_document import LayoutBlock, LayoutPageCoordinates, LayoutToken
from pygrobid.document.semantic_document import (
    SemanticDocument,
    SemanticHeading,
    SemanticParagraph,
    SemanticSection
)


LOGGER = logging.getLogger(__name__)


TEI_NS = 'http://www.tei-c.org/ns/1.0'
TEI_NS_PREFIX = '{%s}' % TEI_NS

TEI_NS_MAP = {
    'tei': TEI_NS
}

TEI_E = ElementMaker(namespace=TEI_NS, nsmap={
    None: TEI_NS
})


class TagExpression:
    def __init__(self, tag: str, attrib: Dict[str, str]):
        self.tag = tag
        self.attrib = attrib

    def create_node(self):
        try:
            return TEI_E(self.tag, self.attrib)
        except ValueError as e:
            raise ValueError(
                'failed to create node with tag=%r, attrib=%r due to %s' % (
                    self.tag, self.attrib, e
                )
            ) from e


def _parse_tag_expression(tag_expression):
    match = re.match(r'^([^\[]+)(\[@?([^=]+)="(.+)"\])?$', tag_expression)
    if not match:
        raise ValueError('invalid tag expression: %s' % tag_expression)
    LOGGER.debug('match: %s', match.groups())
    tag_name = match.group(1)
    if match.group(2):
        attrib = {match.group(3): match.group(4)}
    else:
        attrib = {}
    return TagExpression(tag=tag_name, attrib=attrib)


def get_or_create_element_at(parent: etree.ElementBase, path: List[str]) -> etree.ElementBase:
    if not path:
        return parent
    child = parent.find(TEI_NS_PREFIX + path[0])
    if child is None:
        LOGGER.debug('creating element: %s', path[0])
        tag_expression = _parse_tag_expression(path[0])
        child = tag_expression.create_node()
        parent.append(child)
    return get_or_create_element_at(child, path[1:])


def get_text_content(node: etree.ElementBase) -> str:
    if node is None:
        return ''
    return ''.join(node.itertext())


def tei_xpath(parent: etree.ElementBase, xpath: str) -> List[etree.ElementBase]:
    return parent.xpath(xpath, namespaces=TEI_NS_MAP)


def get_tei_xpath_text_content_list(parent: etree.ElementBase, xpath: str) -> List[str]:
    return [get_text_content(node) for node in tei_xpath(parent, xpath)]


def get_required_styles(layout_token: LayoutToken) -> List[str]:
    required_styles = []
    if layout_token.font.is_bold:
        required_styles.append('bold')
    if layout_token.font.is_italics:
        required_styles.append('italic')
    return required_styles


def get_element_for_styles(styles: List[str], text: str) -> etree.ElementBase:
    if not styles:
        return text
    child: Optional[etree.ElementBase] = None
    for style in reversed(styles):
        LOGGER.debug('style: %r, child: %r, text: %r', style, child, text)
        if child is not None:
            child = TEI_E.hi({'rend': style}, child)
        else:
            child = TEI_E.hi({'rend': style}, text)
    return child


def format_coordinates(coordinates: LayoutPageCoordinates) -> str:
    return '%d,%.2f,%.2f,%.2f,%.2f' % (
        coordinates.page_number,
        coordinates.x,
        coordinates.y,
        coordinates.width,
        coordinates.height
    )


def format_coordinates_list(coordinates_list: List[LayoutPageCoordinates]) -> str:
    return ';'.join((
        format_coordinates(coordinates)
        for coordinates in coordinates_list
    ))


def iter_layout_block_tei_children(
    layout_block: LayoutBlock,
    enable_coordinates: bool = True
) -> Iterable[Union[str, etree.ElementBase]]:
    pending_styles: List[str] = []
    pending_text = ''
    pending_whitespace = ''
    if enable_coordinates:
        yield {
            'coords': format_coordinates_list(
                layout_block.get_merged_coordinates_list()
            )
        }
    for line in layout_block.lines:
        for token in line.tokens:
            required_styles = get_required_styles(token)
            LOGGER.debug('token: %r, required_styles=%r', token, required_styles)
            if required_styles != pending_styles:
                if pending_text:
                    yield get_element_for_styles(
                        pending_styles,
                        pending_text
                    )
                    pending_text = ''
                if pending_whitespace:
                    yield pending_whitespace
                    pending_whitespace = ''
                pending_styles = required_styles
            if pending_whitespace:
                pending_text += pending_whitespace
                pending_whitespace = ''
            pending_text += token.text
            pending_whitespace = token.whitespace
    if pending_text:
        yield get_element_for_styles(
            pending_styles,
            pending_text
        )


def extend_element(
    element: etree.ElementBase,
    children_or_attributes: Iterable[etree.ElementBase]
):
    for item in children_or_attributes:
        if isinstance(item, dict):
            element.attrib.update(item)
            continue
        if isinstance(item, str):
            children = list(element)
            previous_element = children[-1] if children else None
            if previous_element is not None:
                previous_element.tail = (
                    (previous_element.tail or '')
                    + item
                )
            else:
                element.text = (
                    (element.text or '')
                    + item
                )
            continue
        element.append(item)


class TeiElementWrapper:
    def __init__(self, element: etree.ElementBase):
        self.element = element

    def xpath_nodes(self, xpath: str) -> List[etree.ElementBase]:
        return tei_xpath(self.element, xpath)

    def xpath(self, xpath: str) -> List['TeiElementWrapper']:
        return [TeiElementWrapper(node) for node in self.xpath_nodes(xpath)]

    def get_xpath_text_content_list(self, xpath: str) -> List[str]:
        return get_tei_xpath_text_content_list(self.element, xpath)

    def get_notes_text_list(self, note_type: str) -> List[str]:
        return get_tei_xpath_text_content_list(
            self.element,
            '//tei:note[@type="%s"]' % note_type,
        )

    def add_note(self, note_type: str, layout_block: LayoutBlock):
        self.element.append(
            TEI_E.note(
                {'type': note_type},
                *iter_layout_block_tei_children(layout_block)
            )
        )


class TeiSectionParagraph(TeiElementWrapper):
    def __init__(self, element: etree.ElementBase):
        super().__init__(element)
        self._pending_whitespace: Optional[str] = None

    def add_content(self, layout_block: LayoutBlock):
        if self._pending_whitespace:
            extend_element(self.element, [self._pending_whitespace])
        self._pending_whitespace = layout_block.whitespace
        extend_element(
            self.element,
            iter_layout_block_tei_children(layout_block)
        )


class TeiSection(TeiElementWrapper):
    def get_title_text(self) -> str:
        return '\n'.join(get_tei_xpath_text_content_list(
            self.element,
            '//tei:head',
        ))

    def get_paragraph_text_list(self) -> List[str]:
        return get_tei_xpath_text_content_list(
            self.element,
            '//tei:p',
        )

    def add_title(self, layout_block: LayoutBlock):
        self.element.append(
            TEI_E.head(*iter_layout_block_tei_children(layout_block))
        )

    def add_paragraph(self, paragraph: TeiSectionParagraph):
        self.element.append(paragraph.element)

    def create_paragraph(self) -> TeiSectionParagraph:
        return TeiSectionParagraph(TEI_E.p())


class TeiDocument(TeiElementWrapper):
    def __init__(self, root: Optional[etree.ElementBase] = None):
        if root is None:
            self.root = TEI_E.TEI()
        else:
            self.root = root
        super().__init__(self.root)

    def get_or_create_element_at(self, path: List[str]) -> etree.ElementBase:
        return get_or_create_element_at(self.root, path)

    def set_child_element_at(self, path: List[str], child: etree.ElementBase):
        parent = self.get_or_create_element_at(path)
        parent.append(child)

    def get_title(self) -> str:
        return '\n'.join(get_tei_xpath_text_content_list(
            self.root,
            '//tei:fileDesc/tei:titleStmt/tei:title[@level="a"][@type="main"]',
        ))

    def set_title(self, title: str):
        self.set_child_element_at(
            ['teiHeader', 'fileDesc', 'titleStmt'],
            TEI_E.title(title, level="a", type="main")
        )

    def set_title_layout_block(self, title_block: LayoutBlock):
        self.set_child_element_at(
            ['teiHeader', 'fileDesc', 'titleStmt'],
            TEI_E.title(
                {'level': 'a', 'type': 'main'},
                *iter_layout_block_tei_children(title_block)
            )
        )

    def get_abstract(self) -> str:
        return '\n'.join(get_tei_xpath_text_content_list(
            self.root,
            '//tei:abstract/tei:p',
        ))

    def set_abstract(self, abstract: str):
        self.set_child_element_at(
            ['teiHeader', 'profileDesc', 'abstract'],
            TEI_E.p(abstract)
        )

    def set_abstract_layout_block(self, abstract_block: LayoutBlock):
        self.set_child_element_at(
            ['teiHeader', 'profileDesc', 'abstract'],
            TEI_E.p(*iter_layout_block_tei_children(abstract_block))
        )

    def get_body_element(self) -> etree.ElementBase:
        return self.get_or_create_element_at(['text', 'body'])

    def get_body(self) -> TeiElementWrapper:
        return TeiElementWrapper(self.get_body_element())

    def get_back_annex_element(self) -> etree.ElementBase:
        return self.get_or_create_element_at(['text', 'back', 'div[@type="annex"]'])

    def get_back_annex(self) -> TeiElementWrapper:
        return TeiElementWrapper(self.get_back_annex_element())

    def get_body_sections(self) -> List[TeiSection]:
        return [
            TeiSection(element)
            for element in tei_xpath(self.get_body_element(), './tei:div')
        ]

    def add_body_section(self, section: TeiSection):
        self.get_body_element().append(section.element)

    def add_back_annex_section(self, section: TeiSection):
        self.get_back_annex_element().append(section.element)

    def create_section(self) -> TeiSection:
        return TeiSection(TEI_E.div())


def _get_tei_section_for_semantic_section(semantic_section: SemanticSection) -> TeiSection:
    LOGGER.debug('semantic_section: %s', semantic_section)
    tei_section = TeiSection(TEI_E.div())
    for semantic_content in semantic_section:
        if isinstance(semantic_content, SemanticHeading):
            tei_section.add_title(LayoutBlock.for_tokens(
                list(semantic_content.iter_tokens())
            ))
        if isinstance(semantic_content, SemanticParagraph):
            paragraph = tei_section.create_paragraph()
            paragraph.add_content(LayoutBlock.for_tokens(
                list(semantic_content.iter_tokens())
            ))
            tei_section.add_paragraph(paragraph)
    return tei_section


def get_tei_for_semantic_document(semantic_document: SemanticDocument) -> TeiDocument:
    LOGGER.debug('semantic_document: %s', semantic_document)
    tei_document = TeiDocument()
    title_block = semantic_document.meta.title.merged_block
    if title_block:
        tei_document.set_title_layout_block(title_block)
    abstract_block = semantic_document.meta.abstract.merged_block
    if abstract_block:
        tei_document.set_abstract_layout_block(abstract_block)
    for semantic_section in semantic_document.body_section.sections:
        tei_section = _get_tei_section_for_semantic_section(semantic_section)
        tei_document.add_body_section(tei_section)
    for semantic_section in semantic_document.back_section.sections:
        tei_section = _get_tei_section_for_semantic_section(semantic_section)
        tei_document.add_back_annex_section(tei_section)
    return tei_document
