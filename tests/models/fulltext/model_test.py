from pygrobid.document.layout_document import (
    LayoutBlock
)
from pygrobid.document.tei_document import TeiDocument

from pygrobid.models.fulltext.model import (
    FullTextModel
)


SECTION_TITLE_1 = 'the title 1'

SECTION_PARAGRAPH_1 = 'the paragraph 1'
SECTION_PARAGRAPH_2 = 'the paragraph 2'
SECTION_PARAGRAPH_3 = 'the paragraph 3'


class TestFullTextModel:
    def test_should_add_section_title_and_paragraph(self):
        document = TeiDocument()
        fulltext_model = FullTextModel('dummy-path')
        fulltext_model.update_document_with_entity_blocks(
            document,
            [
                ('<section>', LayoutBlock.for_text(SECTION_TITLE_1)),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1))
            ]
        )
        sections = document.get_body_sections()
        assert len(sections) == 1
        assert sections[0].get_title_text() == SECTION_TITLE_1
        assert sections[0].get_paragraph_text_list() == [SECTION_PARAGRAPH_1]

    def test_should_add_paragraphs_without_title(self):
        document = TeiDocument()
        fulltext_model = FullTextModel('dummy-path')
        fulltext_model.update_document_with_entity_blocks(
            document,
            [
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_2))
            ]
        )
        sections = document.get_body_sections()
        assert len(sections) == 1
        assert sections[0].get_paragraph_text_list() == [
            SECTION_PARAGRAPH_1,
            SECTION_PARAGRAPH_2
        ]

    def test_should_include_citation_in_paragraph(self):
        document = TeiDocument()
        fulltext_model = FullTextModel('dummy-path')
        fulltext_model.update_document_with_entity_blocks(
            document,
            [
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<citation_marker>', LayoutBlock.for_text(SECTION_PARAGRAPH_2)),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_3)),
            ]
        )
        sections = document.get_body_sections()
        assert len(sections) == 1
        assert sections[0].get_paragraph_text_list() == [
            ' '.join([SECTION_PARAGRAPH_1, SECTION_PARAGRAPH_2, SECTION_PARAGRAPH_3])
        ]

    def test_should_add_note_for_other_text_to_section(self):
        document = TeiDocument()
        fulltext_model = FullTextModel('dummy-path')
        fulltext_model.update_document_with_entity_blocks(
            document,
            [
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('O', LayoutBlock.for_text(SECTION_PARAGRAPH_2))
            ]
        )
        sections = document.get_body_sections()
        assert len(sections) == 1
        assert sections[0].get_paragraph_text_list() == [SECTION_PARAGRAPH_1]
        assert sections[0].get_notes_text_list('other') == [SECTION_PARAGRAPH_2]

    def test_should_add_note_for_other_text_to_body(self):
        document = TeiDocument()
        fulltext_model = FullTextModel('dummy-path')
        fulltext_model.update_document_with_entity_blocks(
            document,
            [
                ('O', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_2))
            ]
        )
        assert document.get_body().get_notes_text_list('other') == [SECTION_PARAGRAPH_1]
        sections = document.get_body_sections()
        assert len(sections) == 1
        assert sections[0].get_paragraph_text_list() == [SECTION_PARAGRAPH_2]

    def test_should_add_note_for_figure_text_to_section(self):
        document = TeiDocument()
        fulltext_model = FullTextModel('dummy-path')
        fulltext_model.update_document_with_entity_blocks(
            document,
            [
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<figure>', LayoutBlock.for_text(SECTION_PARAGRAPH_2))
            ]
        )
        sections = document.get_body_sections()
        assert len(sections) == 1
        assert sections[0].get_paragraph_text_list() == [SECTION_PARAGRAPH_1]
        assert sections[0].get_notes_text_list('<figure>') == [SECTION_PARAGRAPH_2]

    def test_should_add_note_for_table_text_to_section(self):
        document = TeiDocument()
        fulltext_model = FullTextModel('dummy-path')
        fulltext_model.update_document_with_entity_blocks(
            document,
            [
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<table>', LayoutBlock.for_text(SECTION_PARAGRAPH_2))
            ]
        )
        sections = document.get_body_sections()
        assert len(sections) == 1
        assert sections[0].get_paragraph_text_list() == [SECTION_PARAGRAPH_1]
        assert sections[0].get_notes_text_list('<table>') == [SECTION_PARAGRAPH_2]
