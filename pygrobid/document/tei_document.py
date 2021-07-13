# pylint: disable=too-many-lines
import logging
import re
from typing import (
    Any,
    Callable,
    Iterable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union
)

from lxml import etree
from lxml.builder import ElementMaker

from pygrobid.utils.stop_watch import StopWatchRecorder
from pygrobid.utils.xml import get_text_content
from pygrobid.document.layout_document import LayoutBlock, LayoutPageCoordinates, LayoutToken
from pygrobid.document.semantic_document import (
    SemanticAbstract,
    SemanticAddressField,
    SemanticAddressLine,
    SemanticAffiliationAddress,
    SemanticAuthor,
    SemanticCaption,
    SemanticCitation,
    SemanticContentWrapper,
    SemanticCountry,
    SemanticDate,
    SemanticDepartment,
    SemanticDocument,
    SemanticExternalIdentifier,
    SemanticExternalUrl,
    SemanticFigure,
    SemanticFigureCitation,
    SemanticGivenName,
    SemanticHeading,
    SemanticInstitution,
    SemanticIssue,
    SemanticJournal,
    SemanticLabel,
    SemanticLaboratory,
    SemanticLocation,
    SemanticMarker,
    SemanticMiddleName,
    SemanticMixedContentWrapper,
    SemanticNameSuffix,
    SemanticNameTitle,
    SemanticNote,
    SemanticPageRange,
    SemanticParagraph,
    SemanticPostBox,
    SemanticPostCode,
    SemanticPublisher,
    SemanticRawEditors,
    SemanticRawReference,
    SemanticRawReferenceText,
    SemanticReference,
    SemanticReferenceCitation,
    SemanticReferenceList,
    SemanticRegion,
    SemanticSection,
    SemanticSectionTypes,
    SemanticSettlement,
    SemanticSurname,
    SemanticTable,
    SemanticTableCitation,
    SemanticTextContentWrapper,
    SemanticTitle,
    SemanticVolume
)


LOGGER = logging.getLogger(__name__)


XML_NS = 'http://www.w3.org/XML/1998/namespace'
XML_NS_PREFIX = '{%s}' % XML_NS
XML_ID = XML_NS_PREFIX + 'id'

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

    def create_node(self, *args):
        try:
            return TEI_E(self.tag, self.attrib, *args)
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
            child = TEI_E('hi', {'rend': style}, child)
        else:
            child = TEI_E('hi', {'rend': style}, text)
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


def get_default_attributes_for_layout_block(
    layout_block: LayoutBlock,
    enable_coordinates: bool = True
) -> Dict[str, str]:
    if enable_coordinates:
        formatted_coords = format_coordinates_list(
            layout_block.get_merged_coordinates_list()
        )
        if formatted_coords:
            return {'coords': formatted_coords}
    return {}


def iter_layout_block_tei_children(
    layout_block: LayoutBlock,
    enable_coordinates: bool = True
) -> Iterable[Union[str, etree.ElementBase]]:
    pending_styles: List[str] = []
    pending_text = ''
    pending_whitespace = ''
    if enable_coordinates:
        yield get_default_attributes_for_layout_block(
            layout_block=layout_block,
            enable_coordinates=enable_coordinates
        )
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
            try:
                previous_element = element[-1]
            except IndexError:
                previous_element = None
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


def _create_tei_note_element(
    note_type: str,
    layout_block: LayoutBlock
) -> etree.EntityBase:
    return TEI_E(
        'note',
        {'type': note_type},
        *iter_layout_block_tei_children(layout_block)
    )


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
        self.element.append(_create_tei_note_element(note_type, layout_block))


class TeiElementBuilder:
    def __init__(
        self,
        element: etree.ElementBase,
    ):
        self.element = element
        self.builder_by_path_fragment: Dict[str, 'TeiElementBuilder'] = {}

    def get_or_create(
        self,
        path: Optional[List[str]]
    ) -> 'TeiElementBuilder':
        if not path:
            return self
        key = path[0]
        builder = self.builder_by_path_fragment.get(key)
        if not builder:
            builder = TeiElementBuilder(TEI_E(key))
            self.element.append(builder.element)
            self.builder_by_path_fragment[key] = builder
        return builder.get_or_create(path[1:])

    def add_dict(self, attrib: dict):
        _attrib = self.element.attrib
        for k, v in attrib.items():
            _attrib[k] = v

    def append(
        self,
        child: Union[dict, etree.ElementBase]
    ):
        if isinstance(child, dict):
            self.add_dict(child)
            return
        self.element.append(child)


class TeiAuthor(TeiElementWrapper):
    pass


class TeiAffiliation(TeiElementWrapper):
    pass


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

    def add_paragraph(self, paragraph: TeiSectionParagraph):
        self.element.append(paragraph.element)

    def create_paragraph(self) -> TeiSectionParagraph:
        return TeiSectionParagraph(TEI_E('p'))


class TeiDocument(TeiElementWrapper):
    def __init__(self, root: Optional[etree.ElementBase] = None):
        if root is None:
            self.root = TEI_E('TEI')
        else:
            self.root = root
        self._reference_element: Optional[etree.ElementBase] = None
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
            TEI_E('title', title, level="a", type="main")
        )

    def set_title_layout_block(self, title_block: LayoutBlock):
        self.set_child_element_at(
            ['teiHeader', 'fileDesc', 'titleStmt'],
            TEI_E(
                'title',
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
            TEI_E('p', abstract)
        )

    def set_abstract_layout_block(self, abstract_block: LayoutBlock):
        self.set_child_element_at(
            ['teiHeader', 'profileDesc', 'abstract'],
            TEI_E('p', *iter_layout_block_tei_children(abstract_block))
        )

    def get_body_element(self) -> etree.ElementBase:
        return self.get_or_create_element_at(['text', 'body'])

    def get_body(self) -> TeiElementWrapper:
        return TeiElementWrapper(self.get_body_element())

    def get_back_element(self) -> etree.ElementBase:
        return self.get_or_create_element_at(['text', 'back'])

    def get_back_annex_element(self) -> etree.ElementBase:
        return self.get_or_create_element_at(['text', 'back', 'div[@type="annex"]'])

    def get_back_annex(self) -> TeiElementWrapper:
        return TeiElementWrapper(self.get_back_annex_element())

    def get_references_element(self) -> etree.ElementBase:
        if self._reference_element is not None:
            return self._reference_element
        self._reference_element = self.get_or_create_element_at(
            ['text', 'back', 'div[@type="references"]']
        )
        return self._reference_element

    def get_references(self) -> TeiElementWrapper:
        return TeiElementWrapper(self.get_references_element())

    def get_body_sections(self) -> List[TeiSection]:
        return [
            TeiSection(element)
            for element in tei_xpath(self.get_body_element(), './tei:div')
        ]

    def add_body_section(self, section: TeiSection):
        self.get_body_element().append(section.element)

    def add_back_annex_section(self, section: TeiSection):
        self.get_back_annex_element().append(section.element)

    def add_acknowledgement_section(self, section: TeiSection):
        section.element.attrib['type'] = 'acknowledgement'
        self.get_back_element().append(section.element)

    def create_section(self) -> TeiSection:
        return TeiSection(TEI_E('div'))


def get_default_attributes_for_semantic_content(
    semantic_content: SemanticContentWrapper
) -> Dict[str, str]:
    attrib = get_default_attributes_for_layout_block(semantic_content.merged_block)
    if isinstance(semantic_content, SemanticMixedContentWrapper):
        if semantic_content.content_id:
            attrib = {
                **attrib,
                XML_ID: semantic_content.content_id
            }
    return attrib


def get_tei_biblscope_for_page_range(
    page_range: SemanticContentWrapper
) -> etree.ElementBase:
    assert isinstance(page_range, SemanticPageRange)
    if not page_range.from_page or not page_range.to_page:
        return TEI_E(
            'biblScope',
            {'unit': 'page'},
            page_range.get_text()
        )
    return TEI_E(
        'biblScope',
        {
            'unit': 'page',
            'from': page_range.from_page,
            'to': page_range.to_page
        }
    )


def get_tei_element_for_external_reference(
    external_identifier: SemanticContentWrapper
) -> etree.ElementBase:
    assert isinstance(external_identifier, SemanticExternalIdentifier)
    return TEI_E(
        'idno',
        {'type': external_identifier.external_identifier_type},
        external_identifier.value
    )


CITATION_TYPE_BY_SEMANTIC_CLASS: Mapping[Type[Any], str] = {
    SemanticFigureCitation: 'figure',
    SemanticTableCitation: 'table',
    SemanticReferenceCitation: 'bibr'
}


def get_tei_element_for_citation(
    citation: SemanticContentWrapper
) -> etree.ElementBase:
    assert isinstance(citation, SemanticCitation)
    citation_type = CITATION_TYPE_BY_SEMANTIC_CLASS.get(type(citation))
    attributes = {}
    if citation_type:
        attributes['type'] = citation_type
    if citation.target_content_id:
        attributes['target'] = '#' + citation.target_content_id
    return TEI_E(
        'ref',
        attributes,
        *iter_layout_block_tei_children(citation.merged_block)
    )


def get_tei_element_for_figure(semantic_figure: SemanticContentWrapper) -> etree.ElementBase:
    LOGGER.debug('semantic_figure: %s', semantic_figure)
    assert isinstance(semantic_figure, SemanticFigure)
    children = [get_default_attributes_for_semantic_content(semantic_figure)]
    for semantic_content in semantic_figure:
        if isinstance(semantic_content, SemanticLabel):
            layout_block = semantic_content.merged_block
            children.append(TEI_E('head', *iter_layout_block_tei_children(layout_block)))
            children.append(TEI_E('label', *iter_layout_block_tei_children(layout_block)))
            continue
        if isinstance(semantic_content, SemanticCaption):
            children.append(TEI_E(
                'figDesc', *iter_layout_block_tei_children(semantic_content.merged_block)
            ))
            continue
        children.append(get_tei_child_element_for_semantic_content(semantic_content))
    return TEI_E('figure', *children)


def get_tei_element_for_table(semantic_table: SemanticContentWrapper) -> etree.ElementBase:
    LOGGER.debug('semantic_table: %s', semantic_table)
    assert isinstance(semantic_table, SemanticTable)
    children = [get_default_attributes_for_semantic_content(semantic_table)]
    for semantic_content in semantic_table:
        if isinstance(semantic_content, SemanticLabel):
            layout_block = semantic_content.merged_block
            children.append(TEI_E('head', *iter_layout_block_tei_children(layout_block)))
            children.append(TEI_E('label', *iter_layout_block_tei_children(layout_block)))
            continue
        if isinstance(semantic_content, SemanticCaption):
            children.append(TEI_E(
                'figDesc', *iter_layout_block_tei_children(semantic_content.merged_block)
            ))
            continue
        children.append(get_tei_child_element_for_semantic_content(semantic_content))
    return TEI_E('figure', {'type': 'table'}, *children)


def get_tei_element_for_heading(
    semantic_heading: SemanticContentWrapper
) -> etree.ElementBase:
    LOGGER.debug('semantic_heading: %s', semantic_heading)
    assert isinstance(semantic_heading, SemanticHeading)
    children: T_ElementChildrenList = [
        get_default_attributes_for_semantic_content(semantic_heading)
    ]
    pending_whitespace = ''
    for semantic_content in semantic_heading:
        if isinstance(semantic_content, SemanticLabel):
            children.append({'n': semantic_content.get_text().rstrip('.')})
            continue
        layout_block = semantic_content.merged_block
        if pending_whitespace:
            children.append(pending_whitespace)
        children.extend(iter_layout_block_tei_children(
            layout_block=layout_block,
            enable_coordinates=False
        ))
        pending_whitespace = layout_block.whitespace
    return TEI_E('head', *children)


def get_tei_element_for_paragraph(
    semantic_paragraph: SemanticContentWrapper
) -> etree.ElementBase:
    LOGGER.debug('semantic_paragraph: %s', semantic_paragraph)
    assert isinstance(semantic_paragraph, SemanticParagraph)
    children: T_ElementChildrenList = [
        get_default_attributes_for_semantic_content(semantic_paragraph)
    ]
    pending_whitespace = ''
    for semantic_content in semantic_paragraph:
        pending_whitespace = append_tei_children_list_and_get_whitespace(
            children,
            semantic_content,
            pending_whitespace=pending_whitespace
        )
    return TEI_E('p', *children)


def get_tei_element_for_semantic_section(
    semantic_section: SemanticContentWrapper
) -> etree.ElementBase:
    LOGGER.debug('semantic_section: %s', semantic_section)
    assert isinstance(semantic_section, SemanticSection)
    tei_section = TeiSection(TEI_E('div'))
    for semantic_content in semantic_section:
        if isinstance(semantic_content, (SemanticFigure, SemanticTable,)):
            # rendered at parent level
            continue
        tei_section.element.append(get_tei_child_element_for_semantic_content(
            semantic_content
        ))
    return tei_section.element


SIMPLE_TAG_EXPRESSION_BY_SEMANTIC_CONTENT_CLASS = {
    SemanticNameTitle: 'roleName',
    SemanticGivenName: 'forename[@type="first"]',
    SemanticMiddleName: 'forename[@type="middle"]',
    SemanticSurname: 'surname',
    SemanticNameSuffix: 'genName',
    SemanticRawEditors: 'editor',
    SemanticMarker: 'note[@type="marker"]',
    SemanticInstitution: 'orgName[@type="institution"]',
    SemanticDepartment: 'orgName[@type="department"]',
    SemanticLaboratory: 'orgName[@type="laboratory"]',
    SemanticAddressLine: 'addrLine',
    SemanticPostCode: 'postCode',
    SemanticPostBox: 'postBox',
    SemanticSettlement: 'settlement',
    SemanticRegion: 'region',
    SemanticCountry: 'country',
    SemanticJournal: 'title[@level="j"]',
    SemanticVolume: 'biblScope[@unit="volume"]',
    SemanticIssue: 'biblScope[@unit="issue"]',
    SemanticPublisher: 'publisher',
    SemanticLocation: 'addrLine',
    SemanticExternalUrl: 'ref[@type="url"]'
}


PARSED_TAG_EXPRESSION_BY_SEMANTIC_CONTENT_CLASS: Dict[type, TagExpression] = {
    key: _parse_tag_expression(value)
    for key, value in SIMPLE_TAG_EXPRESSION_BY_SEMANTIC_CONTENT_CLASS.items()
}


PARENT_PATH_BY_SEMANTIC_CONTENT_CLASS = {
    SemanticTitle: ['analytic'],
    SemanticAuthor: ['analytic'],
    SemanticRawEditors: ['monogr'],
    SemanticExternalIdentifier: ['analytic'],
    SemanticJournal: ['monogr'],
    SemanticVolume: ['monogr', 'imprint'],
    SemanticIssue: ['monogr', 'imprint'],
    SemanticPageRange: ['monogr', 'imprint'],
    SemanticPublisher: ['monogr', 'imprint'],
    SemanticLocation: ['monogr', 'meeting', 'address']
}


ELEMENT_FACTORY_BY_SEMANTIC_CONTENT_CLASS: Mapping[
    Type[Any],
    Callable[[SemanticContentWrapper], etree.ElementBase]
] = {
    SemanticPageRange: get_tei_biblscope_for_page_range,
    SemanticExternalIdentifier: get_tei_element_for_external_reference,
    SemanticFigure: get_tei_element_for_figure,
    SemanticTable: get_tei_element_for_table,
    SemanticFigureCitation: get_tei_element_for_citation,
    SemanticTableCitation: get_tei_element_for_citation,
    SemanticReferenceCitation: get_tei_element_for_citation,
    SemanticHeading: get_tei_element_for_heading,
    SemanticParagraph: get_tei_element_for_paragraph,
    SemanticSection: get_tei_element_for_semantic_section
}


def get_tei_note_for_semantic_content(
    semantic_content: SemanticContentWrapper
) -> etree.ElementBase:
    note_type = 'other'
    if isinstance(semantic_content, SemanticNote):
        note_type = semantic_content.note_type
    else:
        note_type = 'other:' + type(semantic_content).__name__
    return _create_tei_note_element(note_type, semantic_content.merged_block)


def get_tei_child_element_for_semantic_content(
    semantic_content: SemanticContentWrapper
) -> etree.ElementBase:
    semantic_type = type(semantic_content)
    element_factory = ELEMENT_FACTORY_BY_SEMANTIC_CONTENT_CLASS.get(
        semantic_type
    )
    if element_factory:
        return element_factory(semantic_content)
    parsed_tag_expression = PARSED_TAG_EXPRESSION_BY_SEMANTIC_CONTENT_CLASS.get(
        semantic_type
    )
    if parsed_tag_expression:
        return parsed_tag_expression.create_node(
            *iter_layout_block_tei_children(semantic_content.merged_block)
        )
    return get_tei_note_for_semantic_content(semantic_content)


def get_tei_children_and_whitespace_for_semantic_content(
    semantic_content: SemanticContentWrapper
) -> Tuple[List[Union[dict, str, etree.ElementBase]], str]:
    layout_block = semantic_content.merged_block
    if isinstance(semantic_content, SemanticTextContentWrapper):
        return (
            list(iter_layout_block_tei_children(layout_block)),
            layout_block.whitespace
        )
    return (
        [get_tei_child_element_for_semantic_content(semantic_content)],
        layout_block.whitespace
    )


def append_tei_children_and_get_whitespace(
    parent: etree.ElementBase,
    semantic_content: SemanticContentWrapper
) -> str:
    children, whitespace = get_tei_children_and_whitespace_for_semantic_content(
        semantic_content
    )
    extend_element(parent, children)
    return whitespace


T_ElementChildrenListItem = Union[dict, str, etree.ElementBase]
T_ElementChildrenList = List[T_ElementChildrenListItem]


def append_tei_children_list_and_get_whitespace(
    children: T_ElementChildrenList,
    semantic_content: SemanticContentWrapper,
    pending_whitespace: str
) -> str:
    tail_children, tail_whitespace = get_tei_children_and_whitespace_for_semantic_content(
        semantic_content
    )
    if not tail_children:
        return pending_whitespace
    if pending_whitespace:
        children.append(pending_whitespace)
    children.extend(tail_children)
    return tail_whitespace


def _get_tei_raw_affiliation_element_for_semantic_affiliation_address(
    semantic_affiliation_address: SemanticAffiliationAddress
) -> etree.ElementBase:
    children: List[Union[str, dict, etree.ElementBase]] = []
    children.append({'type': 'raw_affiliation'})
    for semantic_content in semantic_affiliation_address:
        merged_block = semantic_content.merged_block
        if isinstance(semantic_content, SemanticMarker):
            children.append(TEI_E(
                'label',
                *iter_layout_block_tei_children(merged_block, enable_coordinates=False)
            ))
            children.append(merged_block.whitespace)
            continue
        children.extend(*iter_layout_block_tei_children(merged_block, enable_coordinates=False))
    return TEI_E('note', *children)


def _get_tei_affiliation_for_semantic_affiliation_address(
    semantic_affiliation_address: SemanticAffiliationAddress
) -> TeiAffiliation:
    LOGGER.debug('semantic_affiliation_address: %s', semantic_affiliation_address)
    raw_affiliation = _get_tei_raw_affiliation_element_for_semantic_affiliation_address(
        semantic_affiliation_address
    )
    attributes = get_default_attributes_for_layout_block(
        semantic_affiliation_address.merged_block
    )
    if semantic_affiliation_address.content_id:
        attributes = {**attributes, 'key': semantic_affiliation_address.content_id}
        if XML_ID in attributes:
            del attributes[XML_ID]
    children = [
        attributes,
        raw_affiliation
    ]
    address_semantic_content_list = []
    for semantic_content in semantic_affiliation_address:
        if isinstance(semantic_content, SemanticAddressField):
            address_semantic_content_list.append(semantic_content)
            continue
        children.append(get_tei_child_element_for_semantic_content(
            semantic_content
        ))
    LOGGER.debug('address_semantic_content_list: %r', address_semantic_content_list)
    if address_semantic_content_list:
        children.append(TEI_E('address', *[
            get_tei_child_element_for_semantic_content(
                semantic_content
            )
            for semantic_content in address_semantic_content_list
        ]))
    return TeiAffiliation(TEI_E('affiliation', *children))


def _get_tei_author_for_semantic_author(
    semantic_author: SemanticAuthor,
    affiliations_by_marker: Optional[Mapping[str, Sequence[SemanticAffiliationAddress]]] = None
) -> TeiAuthor:
    if affiliations_by_marker is None:
        affiliations_by_marker = {}
    LOGGER.debug('semantic_author: %s', semantic_author)
    pers_name_children = []
    for semantic_content in semantic_author:
        pers_name_children.append(get_tei_child_element_for_semantic_content(
            semantic_content
        ))
    children = [
        TEI_E(
            'persName',
            get_default_attributes_for_layout_block(semantic_author.merged_block),
            *pers_name_children
        )
    ]
    affiliations = []
    for marker_text in semantic_author.view_by_type(SemanticMarker).get_text_list():
        semantic_affiliations = affiliations_by_marker.get(marker_text)
        if not semantic_affiliations:
            LOGGER.warning('affiliation not found for marker: %r', marker_text)
            continue
        for semantic_affiliation in semantic_affiliations:
            affiliations.append(_get_tei_affiliation_for_semantic_affiliation_address(
                semantic_affiliation
            ).element)
    children.extend(affiliations)
    return TeiAuthor(TEI_E('author', *children))


def _get_dummy_tei_author_for_semantic_affiliations(
    semantic_affiliations: Sequence[SemanticAffiliationAddress]
) -> TeiAuthor:
    children = [
        TEI_E('note', {'type': 'dummy_author'}, 'Dummy author for orphan affiliations')
    ]
    children.extend([
        _get_tei_affiliation_for_semantic_affiliation_address(
            semantic_affiliation
        ).element
        for semantic_affiliation in semantic_affiliations
    ])
    return TeiAuthor(TEI_E('author', *children))


def get_authors_affiliation_markers(authors: List[SemanticAuthor]) -> Set[str]:
    return {
        marker
        for author in authors
        for marker in author.view_by_type(SemanticMarker).get_text_list()
    }


def get_orphan_affiliations(
    affiliations_by_marker: Dict[str, List[SemanticAffiliationAddress]],
    authors: List[SemanticAuthor]
) -> List[SemanticAffiliationAddress]:
    used_affiliation_markers = get_authors_affiliation_markers(authors)
    return [
        affiliation
        for marker, affiliations in affiliations_by_marker.items()
        if marker not in used_affiliation_markers
        for affiliation in affiliations
    ]


def _get_tei_raw_reference(semantic_raw_ref: SemanticRawReference) -> TeiElementWrapper:
    LOGGER.debug('semantic_raw_ref: %s', semantic_raw_ref)
    children = []
    for semantic_content in semantic_raw_ref:
        if isinstance(semantic_content, SemanticRawReferenceText):
            children.append(_create_tei_note_element(
                'raw_reference', semantic_content.merged_block
            ))
            continue
        children.append(get_tei_child_element_for_semantic_content(semantic_content))
    tei_ref = TeiElementWrapper(TEI_E(
        'biblStruct',
        get_default_attributes_for_semantic_content(semantic_raw_ref),
        *children
    ))
    return tei_ref


def _get_tei_reference(  # pylint: disable=too-many-branches
    semantic_ref: SemanticReference
) -> TeiElementWrapper:
    LOGGER.debug('semantic_ref: %s', semantic_ref)
    tei_ref = TeiElementBuilder(TEI_E(
        'biblStruct',
        get_default_attributes_for_semantic_content(semantic_ref)
    ))
    is_first_date = True
    for semantic_content in semantic_ref:
        parent_path = PARENT_PATH_BY_SEMANTIC_CONTENT_CLASS.get(
            type(semantic_content)
        )
        tei_child_parent = tei_ref.get_or_create(parent_path)
        if isinstance(semantic_content, SemanticLabel):
            tei_child_parent.append(_create_tei_note_element(
                'label', semantic_content.merged_block
            ))
            continue
        if isinstance(semantic_content, SemanticRawReferenceText):
            tei_child_parent.append(_create_tei_note_element(
                'raw_reference', semantic_content.merged_block
            ))
            continue
        if isinstance(semantic_content, SemanticTitle):
            tei_child_parent.append(TEI_E(
                'title',
                {'level': 'a', 'type': 'main'},
                *iter_layout_block_tei_children(
                    semantic_content.merged_block
                )
            ))
            continue
        if isinstance(semantic_content, SemanticAuthor):
            tei_child_parent.append(_get_tei_author_for_semantic_author(
                semantic_content
            ).element)
            continue
        if isinstance(semantic_content, SemanticDate):
            tei_child_parent = tei_ref.get_or_create(['monogr', 'imprint'])
            attrib = {}
            if is_first_date:
                # assume first date is published date (more or less matches GROBID)
                attrib['type'] = 'published'
            if semantic_content.year:
                attrib['when'] = str(semantic_content.year)
            tei_child_parent.append(TEI_E(
                'date', attrib,
                *iter_layout_block_tei_children(layout_block=semantic_content.merged_block)
            ))
            is_first_date = False
            continue
        tei_child_parent.append(get_tei_child_element_for_semantic_content(semantic_content))
    return TeiElementWrapper(tei_ref.element)


def _get_tei_raw_reference_list(
    semantic_reference_list: SemanticReferenceList
) -> TeiElementWrapper:
    tei_reference_list = TeiElementBuilder(TEI_E('listBibl'))
    for semantic_content in semantic_reference_list:
        if isinstance(semantic_content, SemanticRawReference):
            tei_reference_list.append(
                _get_tei_raw_reference(semantic_content).element
            )
            continue
        if isinstance(semantic_content, SemanticReference):
            tei_reference_list.append(
                _get_tei_reference(semantic_content).element
            )
            continue
        tei_reference_list.append(get_tei_child_element_for_semantic_content(
            semantic_content
        ))
    return TeiElementWrapper(tei_reference_list.element)


def get_tei_for_semantic_document(  # pylint: disable=too-many-branches, too-many-statements
    semantic_document: SemanticDocument
) -> TeiDocument:
    stop_watch_recorder = StopWatchRecorder()
    LOGGER.info('generating tei document')
    LOGGER.debug('semantic_document: %s', semantic_document)
    tei_document = TeiDocument()

    stop_watch_recorder.start('front')
    LOGGER.info('generating tei document: front')
    title_block = semantic_document.front.view_by_type(SemanticTitle).merged_block
    if title_block:
        tei_document.set_title_layout_block(title_block)

    abstract_block = semantic_document.front.view_by_type(SemanticAbstract).merged_block
    if abstract_block:
        tei_document.set_abstract_layout_block(abstract_block)

    affiliations_by_marker: Dict[str, List[SemanticAffiliationAddress]] = {}
    for semantic_content in semantic_document.front:
        if isinstance(semantic_content, SemanticAffiliationAddress):
            marker_text = semantic_content.get_text_by_type(SemanticMarker)
            affiliations_by_marker.setdefault(marker_text, []).append(semantic_content)
    LOGGER.debug('affiliations_by_marker: %r', affiliations_by_marker)

    semantic_authors: List[SemanticAuthor] = []
    for semantic_content in semantic_document.front:
        if isinstance(semantic_content, SemanticAuthor):
            semantic_authors.append(semantic_content)
            tei_author = _get_tei_author_for_semantic_author(
                semantic_content,
                affiliations_by_marker=affiliations_by_marker
            )
            tei_document.get_or_create_element_at(
                ['teiHeader', 'fileDesc', 'sourceDesc', 'biblStruct', 'analytic']
            ).append(tei_author.element)
            continue
        if isinstance(semantic_content, SemanticTitle):
            continue
        if isinstance(semantic_content, SemanticAbstract):
            continue
        if isinstance(semantic_content, SemanticAffiliationAddress):
            continue
        tei_document.get_or_create_element_at(
            ['teiHeader']
        ).append(get_tei_note_for_semantic_content(
            semantic_content
        ))
    orphan_affiliations = get_orphan_affiliations(
        affiliations_by_marker=affiliations_by_marker,
        authors=semantic_authors
    )
    if orphan_affiliations:
        dummy_tei_author = _get_dummy_tei_author_for_semantic_affiliations(orphan_affiliations)
        tei_document.get_or_create_element_at(
            ['teiHeader', 'fileDesc', 'sourceDesc', 'biblStruct', 'analytic']
        ).append(dummy_tei_author.element)

    LOGGER.info('generating tei document: body')
    stop_watch_recorder.start('body')
    for semantic_content in semantic_document.body_section:
        if isinstance(semantic_content, SemanticSection):
            tei_section = TeiSection(get_tei_element_for_semantic_section(semantic_content))
            if not list(tei_section.element):
                continue
            tei_document.add_body_section(tei_section)
            continue
        if isinstance(semantic_content, SemanticNote):
            tei_document.get_body().add_note(
                semantic_content.note_type,
                semantic_content.merged_block
            )
            continue
        tei_document.get_body().element.append(get_tei_child_element_for_semantic_content(
            semantic_content
        ))
    for semantic_content in semantic_document.body_section.iter_by_types_recursively(
        (SemanticFigure, SemanticTable,)
    ):
        tei_document.get_body().element.append(get_tei_child_element_for_semantic_content(
            semantic_content
        ))

    LOGGER.info('generating tei document: back section')
    stop_watch_recorder.start('back')
    for semantic_content in semantic_document.back_section:
        if isinstance(semantic_content, SemanticSection):
            tei_section = TeiSection(get_tei_element_for_semantic_section(semantic_content))
            if not list(tei_section.element):
                continue
            if semantic_content.section_type == SemanticSectionTypes.ACKNOWLEDGEMENT:
                tei_document.add_acknowledgement_section(tei_section)
            else:
                tei_document.add_back_annex_section(tei_section)
            continue
        if isinstance(semantic_content, SemanticNote):
            tei_document.get_back_annex().add_note(
                semantic_content.note_type,
                semantic_content.merged_block
            )
            continue
        if isinstance(semantic_content, SemanticReferenceList):
            tei_document.get_references().element.append(
                _get_tei_raw_reference_list(semantic_content).element
            )
            continue
        tei_document.get_back_annex().element.append(get_tei_child_element_for_semantic_content(
            semantic_content
        ))
    for semantic_figure in semantic_document.back_section.iter_by_types_recursively(
        (SemanticFigure, SemanticTable,)
    ):
        tei_document.get_back_annex().element.append(get_tei_child_element_for_semantic_content(
            semantic_figure
        ))
    stop_watch_recorder.stop()
    LOGGER.info('generating tei document done, took: %s', stop_watch_recorder)
    return tei_document
