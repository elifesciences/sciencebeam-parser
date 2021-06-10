import logging

from lxml import etree

from pygrobid.document.layout_document import (
    LayoutBlock,
    LayoutToken,
    LayoutFont
)
from pygrobid.document.semantic_document import SemanticDocument
from pygrobid.document.tei_document import (
    get_text_content,
    get_tei_xpath_text_content_list,
    iter_layout_block_tei_children,
    get_tei_for_semantic_document,
    TeiDocument,
    TEI_E,
    TEI_NS_MAP
)


LOGGER = logging.getLogger(__name__)

TOKEN_1 = 'token1'
TOKEN_2 = 'token2'
TOKEN_3 = 'token3'
TOKEN_4 = 'token4'


ITALICS_FONT_1 = LayoutFont(
    font_id='font1',
    is_italics=True
)

BOLD_FONT_1 = LayoutFont(
    font_id='font1',
    is_bold=True
)

BOLD_ITALICS_FONT_1 = LayoutFont(
    font_id='font1',
    is_bold=True,
    is_italics=True
)


class TestIterLayoutBlockTeiChildren:
    def test_should_add_italic_text(self):
        block = LayoutBlock.for_tokens([
            LayoutToken(TOKEN_1),
            LayoutToken(TOKEN_2, font=ITALICS_FONT_1),
            LayoutToken(TOKEN_3)
        ])
        node = TEI_E.node(*iter_layout_block_tei_children(block))
        assert get_tei_xpath_text_content_list(
            node, './tei:hi[@rend="italic"]'
        ) == [TOKEN_2]
        assert get_text_content(node) == ' '.join([TOKEN_1, TOKEN_2, TOKEN_3])

    def test_should_add_bold_text(self):
        block = LayoutBlock.for_tokens([
            LayoutToken(TOKEN_1),
            LayoutToken(TOKEN_2, font=BOLD_FONT_1),
            LayoutToken(TOKEN_3)
        ])
        node = TEI_E.node(*iter_layout_block_tei_children(block))
        assert get_tei_xpath_text_content_list(
            node, './tei:hi[@rend="bold"]'
        ) == [TOKEN_2]
        assert get_text_content(node) == ' '.join([TOKEN_1, TOKEN_2, TOKEN_3])

    def test_should_add_bold_and_italics_text(self):
        block = LayoutBlock.for_tokens([
            LayoutToken(TOKEN_1),
            LayoutToken(TOKEN_2, font=BOLD_ITALICS_FONT_1),
            LayoutToken(TOKEN_3)
        ])
        node = TEI_E.node(*iter_layout_block_tei_children(block))
        LOGGER.debug('xml: %r', etree.tostring(node))
        assert get_tei_xpath_text_content_list(
            node, './/tei:hi[@rend="bold"]'
        ) == [TOKEN_2]
        assert get_tei_xpath_text_content_list(
            node, './/tei:hi[@rend="italic"]'
        ) == [TOKEN_2]
        assert get_text_content(node) == ' '.join([TOKEN_1, TOKEN_2, TOKEN_3])

    def test_should_combine_bold_and_italics_tokens(self):
        block = LayoutBlock.for_tokens([
            LayoutToken(TOKEN_1),
            LayoutToken(TOKEN_2, font=BOLD_ITALICS_FONT_1),
            LayoutToken(TOKEN_3, font=BOLD_ITALICS_FONT_1),
            LayoutToken(TOKEN_4)
        ])
        node = TEI_E.node(*iter_layout_block_tei_children(block))
        LOGGER.debug('xml: %r', etree.tostring(node))
        assert get_tei_xpath_text_content_list(
            node, './/tei:hi[@rend="bold"]'
        ) == [' '.join([TOKEN_2, TOKEN_3])]
        assert get_tei_xpath_text_content_list(
            node, './/tei:hi[@rend="italic"]'
        ) == [' '.join([TOKEN_2, TOKEN_3])]
        assert get_text_content(node) == ' '.join([TOKEN_1, TOKEN_2, TOKEN_3, TOKEN_4])


class TestTeiDocument:
    def test_should_be_able_to_set_title(self):
        document = TeiDocument()
        document.set_title('test')
        LOGGER.debug('xml: %r', etree.tostring(document.root))
        nodes = document.root.xpath(
            '//tei:fileDesc/tei:titleStmt/tei:title[@level="a"][@type="main"]',
            namespaces=TEI_NS_MAP
        )
        assert [e.text for e in nodes] == ['test']
        assert document.get_title() == 'test'

    def test_should_be_able_to_set_abstract(self):
        document = TeiDocument()
        document.set_abstract('test')
        LOGGER.debug('xml: %r', etree.tostring(document.root))
        nodes = document.root.xpath(
            '//tei:abstract/tei:p', namespaces=TEI_NS_MAP
        )
        assert [e.text for e in nodes] == ['test']
        assert document.get_abstract() == 'test'

    def test_should_be_able_to_set_title_with_italic_layout_tokens(self):
        title_block = LayoutBlock.for_tokens([
            LayoutToken('rend'),
            LayoutToken('italic1', font=ITALICS_FONT_1),
            LayoutToken('test')
        ])
        document = TeiDocument()
        document.set_title_layout_block(title_block)
        LOGGER.debug('xml: %r', etree.tostring(document.root))
        nodes = document.root.xpath(
            '//tei:fileDesc/tei:titleStmt/tei:title[@level="a"][@type="main"]',
            namespaces=TEI_NS_MAP
        )
        assert len(nodes) == 1
        title_node = nodes[0]
        assert get_tei_xpath_text_content_list(
            title_node,
            './tei:hi[@rend="italic"]'
        ) == ['italic1']
        assert document.get_title() == 'rend italic1 test'


class TestGetTeiForSemanticDocument:
    def test_should_return_empty_document(self):
        semantic_document = SemanticDocument()
        tei_document = get_tei_for_semantic_document(semantic_document)
        assert not tei_document.xpath('//tei:div')

    def test_should_set_manuscript_title(self):
        semantic_document = SemanticDocument()
        semantic_document.meta.title.add_block_content(LayoutBlock.for_text(TOKEN_1))
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:fileDesc/tei:titleStmt/tei:title[@level="a"][@type="main"]'
        ) == [TOKEN_1]

    def test_should_set_abstract(self):
        semantic_document = SemanticDocument()
        semantic_document.meta.abstract.add_block_content(LayoutBlock.for_text(TOKEN_1))
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:abstract/tei:p'
        ) == [TOKEN_1]

    def test_should_create_body_section(self):
        semantic_document = SemanticDocument()
        section = semantic_document.body_section.add_new_section()
        section.add_heading_block(LayoutBlock.for_text(TOKEN_1))
        paragraph = section.add_new_paragraph()
        paragraph.add_block_content(LayoutBlock.for_text(TOKEN_2))
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:body/tei:div/tei:head'
        ) == [TOKEN_1]
        assert tei_document.get_xpath_text_content_list(
            '//tei:body/tei:div/tei:p'
        ) == [TOKEN_2]
