import logging
import re
from typing import Iterable, Dict, List, Mapping, Optional, Sequence, Set, Union

from lxml import etree
from lxml.builder import ElementMaker

from pygrobid.utils.xml import get_text_content
from pygrobid.document.layout_document import LayoutBlock, LayoutPageCoordinates, LayoutToken
from pygrobid.document.semantic_document import (
    SemanticAbstract,
    SemanticAddressField,
    SemanticAddressLine,
    SemanticAffiliationAddress,
    SemanticAuthor,
    SemanticContentWrapper,
    SemanticCountry,
    SemanticDepartment,
    SemanticDocument,
    SemanticGivenName,
    SemanticHeading,
    SemanticInstitution,
    SemanticLaboratory,
    SemanticMarker,
    SemanticMiddleName,
    SemanticNameSuffix,
    SemanticNameTitle,
    SemanticNote,
    SemanticParagraph,
    SemanticPostBox,
    SemanticPostCode,
    SemanticRawReference,
    SemanticRawReferenceText,
    SemanticRegion,
    SemanticSection,
    SemanticSectionTypes,
    SemanticSettlement,
    SemanticSurname,
    SemanticTitle
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


def _create_tei_note_element(
    note_type: str,
    layout_block: LayoutBlock
) -> etree.EntityBase:
    return TEI_E.note(
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

    def get_back_element(self) -> etree.ElementBase:
        return self.get_or_create_element_at(['text', 'back'])

    def get_back_annex_element(self) -> etree.ElementBase:
        return self.get_or_create_element_at(['text', 'back', 'div[@type="annex"]'])

    def get_back_annex(self) -> TeiElementWrapper:
        return TeiElementWrapper(self.get_back_annex_element())

    def get_references_element(self) -> etree.ElementBase:
        return self.get_or_create_element_at(
            ['text', 'back', 'div[@type="references"]', 'listBibl']
        )

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
        return TeiSection(TEI_E.div())


SIMPLE_TAG_EXPRESSION_BY_SEMANTIC_CONTENT_CLASS = {
    SemanticNameTitle: 'roleName',
    SemanticGivenName: 'forename[@type="first"]',
    SemanticMiddleName: 'forename[@type="middle"]',
    SemanticSurname: 'surname',
    SemanticNameSuffix: 'genName',
    SemanticMarker: 'note[@type="marker"]',
    SemanticInstitution: 'orgName[@type="institution"]',
    SemanticDepartment: 'orgName[@type="department"]',
    SemanticLaboratory: 'orgName[@type="laboratory"]',
    SemanticAddressLine: 'addrLine',
    SemanticPostCode: 'postCode',
    SemanticPostBox: 'postBox',
    SemanticSettlement: 'settlement',
    SemanticRegion: 'region',
    SemanticCountry: 'country'
}


PARSED_TAG_EXPRESSION_BY_SEMANTIC_CONTENT_CLASS: Dict[type, TagExpression] = {
    key: _parse_tag_expression(value)
    for key, value in SIMPLE_TAG_EXPRESSION_BY_SEMANTIC_CONTENT_CLASS.items()
}


def get_tei_child_element_for_semantic_content(
    semantic_content: SemanticContentWrapper
) -> etree.ElementBase:
    parsed_tag_expression = PARSED_TAG_EXPRESSION_BY_SEMANTIC_CONTENT_CLASS.get(
        type(semantic_content)
    )
    if parsed_tag_expression:
        return parsed_tag_expression.create_node(
            *iter_layout_block_tei_children(semantic_content.merged_block)
        )
    note_type = 'other'
    if isinstance(semantic_content, SemanticNote):
        note_type = semantic_content.note_type
    return TEI_E.note(
        {'type': note_type},
        *iter_layout_block_tei_children(semantic_content.merged_block)
    )


def _get_tei_raw_affiliation_element_for_semantic_affiliation_address(
    semantic_affiliation_address: SemanticAffiliationAddress
) -> etree.ElementBase:
    children: List[Union[str, dict, etree.ElementBase]] = []
    children.append({'type': 'raw_affiliation'})
    for semantic_content in semantic_affiliation_address:
        merged_block = semantic_content.merged_block
        if isinstance(semantic_content, SemanticMarker):
            children.append(TEI_E.label(
                *iter_layout_block_tei_children(merged_block, enable_coordinates=False)
            ))
            children.append(merged_block.whitespace)
            continue
        children.extend(*iter_layout_block_tei_children(merged_block, enable_coordinates=False))
    return TEI_E.note(*children)


def _get_tei_affiliation_for_semantic_affiliation_address(
    semantic_affiliation_address: SemanticAffiliationAddress
) -> TeiAffiliation:
    LOGGER.debug('semantic_affiliation_address: %s', semantic_affiliation_address)
    raw_affiliation = _get_tei_raw_affiliation_element_for_semantic_affiliation_address(
        semantic_affiliation_address
    )
    children = [
        get_default_attributes_for_layout_block(
            semantic_affiliation_address.merged_block
        ),
        {'key': semantic_affiliation_address.affiliation_id},
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
        children.append(TEI_E.address(*[
            get_tei_child_element_for_semantic_content(
                semantic_content
            )
            for semantic_content in address_semantic_content_list
        ]))
    return TeiAffiliation(TEI_E.affiliation(*children))


def _get_tei_author_for_semantic_author(
    semantic_author: SemanticAuthor,
    affiliations_by_marker: Mapping[str, Sequence[SemanticAffiliationAddress]]
) -> TeiAuthor:
    LOGGER.debug('semantic_author: %s', semantic_author)
    pers_name_children = []
    for semantic_content in semantic_author:
        pers_name_children.append(get_tei_child_element_for_semantic_content(
            semantic_content
        ))
    children = [
        TEI_E.persName(
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
    return TeiAuthor(TEI_E.author(*children))


def _get_dummy_tei_author_for_semantic_affiliations(
    semantic_affiliations: Sequence[SemanticAffiliationAddress]
) -> TeiAuthor:
    children = [
        TEI_E.note({'type': 'dummy_author'}, 'Dummy author for orphan affiliations')
    ]
    children.extend([
        _get_tei_affiliation_for_semantic_affiliation_address(
            semantic_affiliation
        ).element
        for semantic_affiliation in semantic_affiliations
    ])
    return TeiAuthor(TEI_E.author(*children))


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
        if isinstance(semantic_content, SemanticNote):
            tei_section.add_note(
                semantic_content.note_type,
                semantic_content.merged_block
            )
    return tei_section


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
    tei_ref = TeiElementWrapper(TEI_E.biblStruct(
        {XML_ID: semantic_raw_ref.reference_id},
        *children
    ))
    return tei_ref


def get_tei_for_semantic_document(  # pylint: disable=too-many-branches
    semantic_document: SemanticDocument
) -> TeiDocument:
    LOGGER.debug('semantic_document: %s', semantic_document)
    tei_document = TeiDocument()

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
    orphan_affiliations = get_orphan_affiliations(
        affiliations_by_marker=affiliations_by_marker,
        authors=semantic_authors
    )
    if orphan_affiliations:
        dummy_tei_author = _get_dummy_tei_author_for_semantic_affiliations(orphan_affiliations)
        tei_document.get_or_create_element_at(
            ['teiHeader', 'fileDesc', 'sourceDesc', 'biblStruct', 'analytic']
        ).append(dummy_tei_author.element)

    for semantic_content in semantic_document.body_section:
        if isinstance(semantic_content, SemanticSection):
            tei_section = _get_tei_section_for_semantic_section(semantic_content)
            tei_document.add_body_section(tei_section)
        if isinstance(semantic_content, SemanticNote):
            tei_document.get_body().add_note(
                semantic_content.note_type,
                semantic_content.merged_block
            )

    for semantic_content in semantic_document.back_section:
        if isinstance(semantic_content, SemanticSection):
            tei_section = _get_tei_section_for_semantic_section(semantic_content)
            if semantic_content.section_type == SemanticSectionTypes.ACKNOWLEDGEMENT:
                tei_document.add_acknowledgement_section(tei_section)
            else:
                tei_document.add_back_annex_section(tei_section)
        if isinstance(semantic_content, SemanticNote):
            tei_document.get_back_annex().add_note(
                semantic_content.note_type,
                semantic_content.merged_block
            )
        if isinstance(semantic_content, SemanticRawReference):
            tei_document.get_references().element.append(
                _get_tei_raw_reference(semantic_content).element
            )
    return tei_document
