import logging

from lxml import etree

from pygrobid.document.layout_document import (
    LayoutBlock,
    LayoutToken,
    LayoutFont
)
from pygrobid.document.semantic_document import (
    SemanticAbstract,
    SemanticAddressLine,
    SemanticAffiliationAddress,
    SemanticCountry,
    SemanticDepartment,
    SemanticDocument,
    SemanticAuthor,
    SemanticGivenName,
    SemanticInstitution,
    SemanticLaboratory,
    SemanticMarker,
    SemanticMiddleName,
    SemanticNameSuffix,
    SemanticNameTitle,
    SemanticPostBox,
    SemanticPostCode,
    SemanticRawReference,
    SemanticRawReferenceText,
    SemanticRegion,
    SemanticSectionTypes,
    SemanticSettlement,
    SemanticSurname,
    SemanticTitle
)
from pygrobid.document.tei_document import (
    get_text_content,
    get_tei_xpath_text_content_list,
    iter_layout_block_tei_children,
    _get_tei_affiliation_for_semantic_affiliation_address,
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


class TestGetTeiAffiliationForSemanticAffiliationAddress:
    def test_should_add_all_fields(self):
        semantic_affiliation_address = SemanticAffiliationAddress([
            SemanticInstitution(layout_block=LayoutBlock.for_text('Institution1')),
            SemanticDepartment(layout_block=LayoutBlock.for_text('Department1')),
            SemanticLaboratory(layout_block=LayoutBlock.for_text('Lab1')),
            SemanticAddressLine(layout_block=LayoutBlock.for_text('AddressLine1')),
            SemanticPostCode(layout_block=LayoutBlock.for_text('PostCode1')),
            SemanticPostBox(layout_block=LayoutBlock.for_text('PostBox1')),
            SemanticRegion(layout_block=LayoutBlock.for_text('Region1')),
            SemanticSettlement(layout_block=LayoutBlock.for_text('Settlement1')),
            SemanticCountry(layout_block=LayoutBlock.for_text('Country1')),
        ])
        tei_aff = _get_tei_affiliation_for_semantic_affiliation_address(
            semantic_affiliation_address
        )
        LOGGER.debug('tei_aff: %r', etree.tostring(tei_aff.element))
        assert tei_aff.get_xpath_text_content_list(
            'tei:orgName[@type="institution"]'
        ) == ['Institution1']
        assert tei_aff.get_xpath_text_content_list(
            'tei:orgName[@type="department"]'
        ) == ['Department1']
        assert tei_aff.get_xpath_text_content_list(
            'tei:orgName[@type="laboratory"]'
        ) == ['Lab1']
        assert tei_aff.get_xpath_text_content_list(
            'tei:address/tei:addrLine'
        ) == ['AddressLine1']
        assert tei_aff.get_xpath_text_content_list(
            'tei:address/tei:postCode'
        ) == ['PostCode1']
        assert tei_aff.get_xpath_text_content_list(
            'tei:address/tei:postBox'
        ) == ['PostBox1']
        assert tei_aff.get_xpath_text_content_list(
            'tei:address/tei:region'
        ) == ['Region1']
        assert tei_aff.get_xpath_text_content_list(
            'tei:address/tei:settlement'
        ) == ['Settlement1']
        assert tei_aff.get_xpath_text_content_list(
            'tei:address/tei:country'
        ) == ['Country1']


class TestGetTeiForSemanticDocument:
    def test_should_return_empty_document(self):
        semantic_document = SemanticDocument()
        tei_document = get_tei_for_semantic_document(semantic_document)
        assert not tei_document.xpath('//tei:div')

    def test_should_set_manuscript_title(self):
        semantic_document = SemanticDocument()
        semantic_document.front.add_content(
            SemanticTitle(layout_block=LayoutBlock.for_text(TOKEN_1))
        )
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:fileDesc/tei:titleStmt/tei:title[@level="a"][@type="main"]'
        ) == [TOKEN_1]

    def test_should_set_abstract(self):
        semantic_document = SemanticDocument()
        semantic_document.front.add_content(
            SemanticAbstract(LayoutBlock.for_text(TOKEN_1))
        )
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:abstract/tei:p'
        ) == [TOKEN_1]

    def test_should_add_single_author(self):
        semantic_document = SemanticDocument()
        title = SemanticNameTitle(layout_block=LayoutBlock.for_text('Title1'))
        given_name = SemanticGivenName(layout_block=LayoutBlock.for_text('Given1'))
        middle_name = SemanticMiddleName(layout_block=LayoutBlock.for_text('Middle1'))
        surname = SemanticSurname(layout_block=LayoutBlock.for_text('Surname1'))
        suffix = SemanticNameSuffix(layout_block=LayoutBlock.for_text('Suffix1'))
        author = SemanticAuthor([title, given_name, middle_name, surname, suffix])
        semantic_document.front.add_content(author)
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:author//tei:roleName'
        ) == ['Title1']
        assert tei_document.get_xpath_text_content_list(
            '//tei:author//tei:forename[@type="first"]'
        ) == ['Given1']
        assert tei_document.get_xpath_text_content_list(
            '//tei:author//tei:forename[@type="middle"]'
        ) == ['Middle1']
        assert tei_document.get_xpath_text_content_list(
            '//tei:author//tei:surname'
        ) == ['Surname1']
        assert tei_document.get_xpath_text_content_list(
            '//tei:author//tei:genName'
        ) == ['Suffix1']

    def test_should_add_single_author_with_affiliation(self):
        semantic_document = SemanticDocument()
        title = SemanticNameTitle(layout_block=LayoutBlock.for_text('Title1'))
        given_name = SemanticGivenName(layout_block=LayoutBlock.for_text('Given1'))
        middle_name = SemanticMiddleName(layout_block=LayoutBlock.for_text('Middle1'))
        surname = SemanticSurname(layout_block=LayoutBlock.for_text('Surname1'))
        suffix = SemanticNameSuffix(layout_block=LayoutBlock.for_text('Suffix1'))
        author_marker = SemanticMarker(layout_block=LayoutBlock.for_text('1'))
        author = SemanticAuthor([title, given_name, middle_name, surname, suffix, author_marker])
        aff_marker = SemanticMarker(layout_block=LayoutBlock.for_text('1'))
        institution = SemanticInstitution(layout_block=LayoutBlock.for_text('Institution1'))
        aff = SemanticAffiliationAddress([aff_marker, institution])
        aff.affiliation_id = 'aff0'
        semantic_document.front.add_content(author)
        semantic_document.front.add_content(aff)
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:author//tei:roleName'
        ) == ['Title1']
        assert tei_document.get_xpath_text_content_list(
            '//tei:author//tei:forename[@type="first"]'
        ) == ['Given1']
        assert tei_document.get_xpath_text_content_list(
            '//tei:author//tei:forename[@type="middle"]'
        ) == ['Middle1']
        assert tei_document.get_xpath_text_content_list(
            '//tei:author//tei:surname'
        ) == ['Surname1']
        assert tei_document.get_xpath_text_content_list(
            '//tei:author//tei:genName'
        ) == ['Suffix1']
        assert tei_document.get_xpath_text_content_list(
            '//tei:author/tei:affiliation/tei:note[@type="raw_affiliation"]'
        ) == [aff.get_text()]
        assert tei_document.get_xpath_text_content_list(
            '//tei:author/tei:affiliation/tei:note[@type="raw_affiliation"]/tei:label'
        ) == [aff_marker.get_text()]
        assert tei_document.get_xpath_text_content_list(
            '//tei:author/tei:affiliation/@key'
        ) == ['aff0']
        assert tei_document.get_xpath_text_content_list(
            '//tei:author/tei:affiliation/tei:orgName[@type="institution"]'
        ) == [institution.get_text()]

    def test_should_add_orphan_affiliation(self):
        semantic_document = SemanticDocument()
        aff_marker = SemanticMarker(layout_block=LayoutBlock.for_text('1'))
        institution = SemanticInstitution(layout_block=LayoutBlock.for_text('Institution1'))
        aff = SemanticAffiliationAddress([aff_marker, institution])
        aff.affiliation_id = 'aff0'
        semantic_document.front.add_content(aff)
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:author/tei:affiliation/tei:note[@type="raw_affiliation"]'
        ) == [aff.get_text()]
        assert tei_document.get_xpath_text_content_list(
            '//tei:author/tei:affiliation/tei:note[@type="raw_affiliation"]/tei:label'
        ) == [aff_marker.get_text()]
        assert tei_document.get_xpath_text_content_list(
            '//tei:author/tei:affiliation/@key'
        ) == ['aff0']

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

    def test_should_create_back_section(self):
        semantic_document = SemanticDocument()
        section = semantic_document.back_section.add_new_section()
        section.add_heading_block(LayoutBlock.for_text(TOKEN_1))
        paragraph = section.add_new_paragraph()
        paragraph.add_block_content(LayoutBlock.for_text(TOKEN_2))
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:back/tei:div[@type="annex"]/tei:div/tei:head'
        ) == [TOKEN_1]
        assert tei_document.get_xpath_text_content_list(
            '//tei:back/tei:div[@type="annex"]/tei:div/tei:p'
        ) == [TOKEN_2]

    def test_should_create_acknowledgment_section(self):
        semantic_document = SemanticDocument()
        section = semantic_document.back_section.add_new_section(
            SemanticSectionTypes.ACKNOWLEDGEMENT
        )
        section.add_heading_block(LayoutBlock.for_text(TOKEN_1))
        paragraph = section.add_new_paragraph()
        paragraph.add_block_content(LayoutBlock.for_text(TOKEN_2))
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:back/tei:div[@type="acknowledgement"]/tei:head'
        ) == [TOKEN_1]
        assert tei_document.get_xpath_text_content_list(
            '//tei:back/tei:div[@type="acknowledgement"]/tei:p'
        ) == [TOKEN_2]

    def test_should_add_notes_to_section(self):
        semantic_document = SemanticDocument()
        section = semantic_document.body_section.add_new_section()
        section.add_note(LayoutBlock.for_text(TOKEN_1), 'other')
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:body/tei:div/tei:note[@type="other"]'
        ) == [TOKEN_1]

    def test_should_add_notes_to_body(self):
        semantic_document = SemanticDocument()
        semantic_document.body_section.add_note(LayoutBlock.for_text(TOKEN_1), 'other')
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:body/tei:note[@type="other"]'
        ) == [TOKEN_1]

    def test_should_add_notes_to_back(self):
        semantic_document = SemanticDocument()
        semantic_document.back_section.add_note(LayoutBlock.for_text(TOKEN_1), 'other')
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:back/tei:div[@type="annex"]/tei:note[@type="other"]'
        ) == [TOKEN_1]

    def test_should_add_raw_references(self):
        semantic_document = SemanticDocument()
        semantic_document.back_section.add_content(
            SemanticRawReference([
                SemanticRawReferenceText(layout_block=LayoutBlock.for_text('Reference 1'))
            ])
        )
        tei_document = get_tei_for_semantic_document(semantic_document)
        LOGGER.debug('tei xml: %r', etree.tostring(tei_document.root))
        assert tei_document.get_xpath_text_content_list(
            '//tei:back/tei:div[@type="references"]/tei:listBibl'
            '/tei:biblStruct/tei:note[@type="raw_reference"]'
        ) == ['Reference 1']
