import logging

from pygrobid.document.layout_document import LayoutBlock
from pygrobid.document.semantic_document import (
    SemanticSection
)
from pygrobid.models.fulltext.extract import (
    FullTextSemanticExtractor
)


LOGGER = logging.getLogger(__name__)


SECTION_TITLE_1 = 'the title 1'

SECTION_PARAGRAPH_1 = 'the paragraph 1'
SECTION_PARAGRAPH_2 = 'the paragraph 2'
SECTION_PARAGRAPH_3 = 'the paragraph 3'


class TestFullTextSemanticExtractor:
    def test_should_add_section_title_and_paragraph(self):
        semantic_content_list = list(
            FullTextSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<section>', LayoutBlock.for_text(SECTION_TITLE_1)),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1))
            ])
        )
        assert len(semantic_content_list) == 1
        section = semantic_content_list[0]
        assert isinstance(section, SemanticSection)
        assert section.get_heading_text() == SECTION_TITLE_1
        assert section.get_paragraph_text_list() == [SECTION_PARAGRAPH_1]

    def test_should_add_paragraphs_without_title(self):
        semantic_content_list = list(
            FullTextSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_2))
            ])
        )
        assert len(semantic_content_list) == 1
        section = semantic_content_list[0]
        assert isinstance(section, SemanticSection)
        assert section.get_paragraph_text_list() == [
            SECTION_PARAGRAPH_1,
            SECTION_PARAGRAPH_2
        ]

    def test_should_include_citation_in_paragraph(self):
        semantic_content_list = list(
            FullTextSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<citation_marker>', LayoutBlock.for_text(SECTION_PARAGRAPH_2)),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_3)),
            ])
        )
        LOGGER.debug('semantic_content_list: %s', semantic_content_list)
        assert len(semantic_content_list) == 1
        section = semantic_content_list[0]
        assert isinstance(section, SemanticSection)
        assert section.get_paragraph_text_list() == [
            ' '.join([SECTION_PARAGRAPH_1, SECTION_PARAGRAPH_2, SECTION_PARAGRAPH_3])
        ]

    def test_should_add_note_for_other_text_to_section(self):
        semantic_content_list = list(
            FullTextSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('O', LayoutBlock.for_text(SECTION_PARAGRAPH_2))
            ])
        )
        assert len(semantic_content_list) == 1
        section = semantic_content_list[0]
        assert isinstance(section, SemanticSection)
        assert section.get_paragraph_text_list() == [SECTION_PARAGRAPH_1]
        assert section.get_notes_text_list('other') == [SECTION_PARAGRAPH_2]

    def test_should_add_note_for_other_text_to_body(self):
        semantic_content_list = list(
            FullTextSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('O', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_2))
            ])
        )
        parent_section = SemanticSection(semantic_content_list)
        assert parent_section.get_notes_text_list('other') == [SECTION_PARAGRAPH_1]
        sections = parent_section.sections
        assert len(sections) == 1
        assert sections[0].get_paragraph_text_list() == [SECTION_PARAGRAPH_2]

    def test_should_add_note_for_figure_text_to_section(self):
        semantic_content_list = list(
            FullTextSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<figure>', LayoutBlock.for_text(SECTION_PARAGRAPH_2))
            ])
        )
        assert len(semantic_content_list) == 1
        section = semantic_content_list[0]
        assert isinstance(section, SemanticSection)
        assert section.get_paragraph_text_list() == [SECTION_PARAGRAPH_1]
        assert section.get_notes_text_list('<figure>') == [SECTION_PARAGRAPH_2]

    def test_should_add_note_for_table_text_to_section(self):
        semantic_content_list = list(
            FullTextSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<table>', LayoutBlock.for_text(SECTION_PARAGRAPH_2))
            ])
        )
        assert len(semantic_content_list) == 1
        section = semantic_content_list[0]
        assert isinstance(section, SemanticSection)
        assert section.get_paragraph_text_list() == [SECTION_PARAGRAPH_1]
        assert section.get_notes_text_list('<table>') == [SECTION_PARAGRAPH_2]
