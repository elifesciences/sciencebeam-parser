import logging

from lxml import etree

from sciencebeam_parser.document.layout_document import (
    LayoutBlock
)
from sciencebeam_parser.document.semantic_document import (
    SemanticContentWrapper,
    SemanticExternalIdentifier,
    SemanticExternalIdentifierTypes,
    SemanticHeading,
    SemanticLabel,
    SemanticPageRange,
    SemanticTitle
)
from sciencebeam_parser.document.tei.common import (
    TeiElementWrapper,
    get_text_content
)
from sciencebeam_parser.document.tei.factories import (
    DEFAULT_TEI_ELEMENT_FACTORY_CONTEXT,
    get_tei_child_elements_for_semantic_content
)


LOGGER = logging.getLogger(__name__)


WEB_URL_1 = 'http://host/path'
DOI_1 = '10.1234/test'


def get_tei_child_element_for_semantic_content(
    semantic_content: SemanticContentWrapper
) -> etree.ElementBase:
    children = get_tei_child_elements_for_semantic_content(
        semantic_content,
        context=DEFAULT_TEI_ELEMENT_FACTORY_CONTEXT
    )
    assert len(children) == 1
    return children[0]


class TestGetTeiChildElementForSemanticContent:
    def test_should_create_biblscope_for_page_range_from_to(self):
        result = TeiElementWrapper(get_tei_child_element_for_semantic_content(
            SemanticPageRange(
                layout_block=LayoutBlock.for_text('12-15'),
                from_page='12',
                to_page='15'
            )
        ))
        LOGGER.debug('result: %r', etree.tostring(result.element))
        assert result.get_xpath_text_content_list(
            '/tei:biblScope[@unit="page"]/@from'
        ) == ['12']
        assert result.get_xpath_text_content_list(
            '/tei:biblScope[@unit="page"]/@to'
        ) == ['15']

    def test_should_create_biblscope_for_page_range_without_from_to(self):
        result = TeiElementWrapper(get_tei_child_element_for_semantic_content(
            SemanticPageRange(
                layout_block=LayoutBlock.for_text('12'),
                from_page=None,
                to_page=None
            )
        ))
        LOGGER.debug('result: %r', etree.tostring(result.element))
        assert result.get_xpath_text_content_list(
            '/tei:biblScope[@unit="page"]'
        ) == ['12']


class TestGetTeiExternalIdentifier:
    def test_should_create_idno_for_doi(self):
        semantic_external_identifier = SemanticExternalIdentifier(
            layout_block=LayoutBlock.for_text('Section Title 1'),
            value=DOI_1,
            external_identifier_type=SemanticExternalIdentifierTypes.DOI
        )
        tei_idno = get_tei_child_element_for_semantic_content(semantic_external_identifier)
        LOGGER.debug('tei_idno: %r', etree.tostring(tei_idno))
        assert get_text_content(tei_idno) == DOI_1
        assert tei_idno.attrib['type'] == semantic_external_identifier.external_identifier_type

    def test_should_create_idno_for_unknown_type(self):
        semantic_external_identifier = SemanticExternalIdentifier(
            layout_block=LayoutBlock.for_text('Section Title 1'),
            value='Other1',
            external_identifier_type=None
        )
        tei_idno = get_tei_child_element_for_semantic_content(semantic_external_identifier)
        LOGGER.debug('tei_idno: %r', etree.tostring(tei_idno))
        assert get_text_content(tei_idno) == semantic_external_identifier.value
        assert tei_idno.attrib.get('type') is None


class TestGetTeiHeading:
    def test_should_create_head_for_simple_title(self):
        semantic_heading = SemanticHeading(layout_block=LayoutBlock.for_text('Section Title 1'))
        tei_head = get_tei_child_element_for_semantic_content(semantic_heading)
        LOGGER.debug('tei_head: %r', etree.tostring(tei_head))
        assert get_text_content(tei_head) == 'Section Title 1'
        assert list(tei_head) == []

    def test_should_create_head_for_child_section_title(self):
        semantic_heading = SemanticHeading([
            SemanticTitle(layout_block=LayoutBlock.for_text('Section Title 1'))
        ])
        tei_head = get_tei_child_element_for_semantic_content(semantic_heading)
        LOGGER.debug('tei_head: %r', etree.tostring(tei_head))
        assert get_text_content(tei_head) == 'Section Title 1'
        assert list(tei_head) == []

    def test_should_create_head_for_label_and_section_title(self):
        semantic_heading = SemanticHeading([
            SemanticLabel(layout_block=LayoutBlock.for_text('1')),
            SemanticTitle(layout_block=LayoutBlock.for_text('Section Title 1'))
        ])
        tei_head = get_tei_child_element_for_semantic_content(semantic_heading)
        LOGGER.debug('tei_head: %r', etree.tostring(tei_head))
        assert tei_head.attrib.get('n') == '1'
        assert get_text_content(tei_head) == 'Section Title 1'
        assert list(tei_head) == []

    def test_should_not_strip_dot_from_label(self):
        semantic_heading = SemanticHeading([
            SemanticLabel(layout_block=LayoutBlock.for_text('1.')),
            SemanticTitle(layout_block=LayoutBlock.for_text('Section Title 1'))
        ])
        tei_head = get_tei_child_element_for_semantic_content(semantic_heading)
        LOGGER.debug('tei_head: %r', etree.tostring(tei_head))
        assert tei_head.attrib.get('n') == '1.'
        assert get_text_content(tei_head) == 'Section Title 1'
        assert list(tei_head) == []
