import logging
from typing import Optional, Tuple

from pygrobid.document.layout_document import LayoutBlock
from pygrobid.document.semantic_document import (
    SemanticFigureCitation,
    SemanticHeading,
    SemanticLabel,
    SemanticParagraph,
    SemanticRawFigure,
    SemanticRawTable,
    SemanticReferenceCitation,
    SemanticSection,
    SemanticTableCitation,
    SemanticTitle
)
from pygrobid.models.fulltext.extract import (
    get_section_label_and_title_from_layout_block,
    FullTextSemanticExtractor
)


LOGGER = logging.getLogger(__name__)


SECTION_TITLE_1 = 'the title 1'

SECTION_PARAGRAPH_1 = 'the paragraph 1'
SECTION_PARAGRAPH_2 = 'the paragraph 2'
SECTION_PARAGRAPH_3 = 'the paragraph 3'


def _get_layout_block_text(layout_block: Optional[LayoutBlock]) -> Optional[str]:
    if layout_block is None:
        return None
    return layout_block.text


def _get_section_label_and_title_text_from_layout_block(
    layout_block: LayoutBlock
) -> Tuple[Optional[str], str]:
    (
        section_label_layout_block, section_title_layout_block
    ) = get_section_label_and_title_from_layout_block(layout_block)
    return _get_layout_block_text(section_label_layout_block), section_title_layout_block.text


class TestGetSectionLabelAndTitleFromLayoutBlock:
    def test_should_not_return_section_label_if_block_is_empty(self):
        section_heading_layout_block = LayoutBlock(lines=[])
        (
            section_label_layout_block, section_title_layout_block
        ) = get_section_label_and_title_from_layout_block(section_heading_layout_block)
        assert section_label_layout_block is None
        assert section_title_layout_block == section_heading_layout_block

    def test_should_not_return_section_label_if_section_title_does_not_contain_any(self):
        section_heading_layout_block = LayoutBlock.for_text(SECTION_TITLE_1)
        (
            section_label_layout_block, section_title_layout_block
        ) = get_section_label_and_title_from_layout_block(section_heading_layout_block)
        assert section_label_layout_block is None
        assert section_title_layout_block == section_heading_layout_block

    def test_should_parse_single_number_without_dot_section_label(self):
        section_heading_layout_block = LayoutBlock.for_text('1 ' + SECTION_TITLE_1)
        (
            section_label_text, section_title_text
        ) = _get_section_label_and_title_text_from_layout_block(section_heading_layout_block)
        assert section_label_text == '1'
        assert section_title_text == SECTION_TITLE_1

    def test_should_parse_single_number_with_dot_section_label(self):
        section_heading_layout_block = LayoutBlock.for_text('1. ' + SECTION_TITLE_1)
        (
            section_label_text, section_title_text
        ) = _get_section_label_and_title_text_from_layout_block(section_heading_layout_block)
        assert section_label_text == '1.'
        assert section_title_text == SECTION_TITLE_1

    def test_should_parse_sub_section_number_with_dot_section_label(self):
        section_heading_layout_block = LayoutBlock.for_text('1.2. ' + SECTION_TITLE_1)
        (
            section_label_text, section_title_text
        ) = _get_section_label_and_title_text_from_layout_block(section_heading_layout_block)
        assert section_label_text == '1.2.'
        assert section_title_text == SECTION_TITLE_1

    def test_should_parse_sub_sub_section_number_with_dot_section_label(self):
        section_heading_layout_block = LayoutBlock.for_text('1.2.3. ' + SECTION_TITLE_1)
        (
            section_label_text, section_title_text
        ) = _get_section_label_and_title_text_from_layout_block(section_heading_layout_block)
        assert section_label_text == '1.2.3.'
        assert section_title_text == SECTION_TITLE_1


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
        semantic_headings = list(section.iter_by_type(SemanticHeading))
        assert len(semantic_headings) == 1
        assert semantic_headings[0].get_text_by_type(SemanticLabel) == ''
        assert semantic_headings[0].get_text_by_type(SemanticTitle) == SECTION_TITLE_1
        assert section.get_paragraph_text_list() == [SECTION_PARAGRAPH_1]

    def test_should_add_separate_section_label(self):
        semantic_content_list = list(
            FullTextSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<section>', LayoutBlock.for_text('1 ' + SECTION_TITLE_1)),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1))
            ])
        )
        assert len(semantic_content_list) == 1
        section = semantic_content_list[0]
        assert isinstance(section, SemanticSection)
        semantic_headings = list(section.iter_by_type(SemanticHeading))
        assert len(semantic_headings) == 1
        assert semantic_headings[0].get_text_by_type(SemanticLabel) == '1'
        assert semantic_headings[0].get_text_by_type(SemanticTitle) == SECTION_TITLE_1

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

    def test_should_include_figure_citation_in_paragraph(self):
        semantic_content_list = list(
            FullTextSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<figure_marker>', LayoutBlock.for_text('Figure 1')),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_2)),
            ])
        )
        LOGGER.debug('semantic_content_list: %s', semantic_content_list)
        assert len(semantic_content_list) == 1
        section = semantic_content_list[0]
        assert isinstance(section, SemanticSection)
        paragraphs = list(section.iter_by_type(SemanticParagraph))
        figure_citations = [
            citation
            for paragraph in paragraphs
            for citation in section.iter_by_type_recursively(SemanticFigureCitation)
        ]
        assert len(figure_citations) == 1
        assert figure_citations[0].get_text() == 'Figure 1'

    def test_should_include_table_citation_in_paragraph(self):
        semantic_content_list = list(
            FullTextSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<table_marker>', LayoutBlock.for_text('Table 1')),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_2)),
            ])
        )
        LOGGER.debug('semantic_content_list: %s', semantic_content_list)
        assert len(semantic_content_list) == 1
        section = semantic_content_list[0]
        assert isinstance(section, SemanticSection)
        paragraphs = list(section.iter_by_type(SemanticParagraph))
        table_citations = [
            citation
            for paragraph in paragraphs
            for citation in section.iter_by_type_recursively(SemanticTableCitation)
        ]
        assert len(table_citations) == 1
        assert table_citations[0].get_text() == 'Table 1'

    def test_should_include_reference_citation_in_paragraph(self):
        semantic_content_list = list(
            FullTextSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_1)),
                ('<citation_marker>', LayoutBlock.for_text('Ref 1')),
                ('<paragraph>', LayoutBlock.for_text(SECTION_PARAGRAPH_2)),
            ])
        )
        LOGGER.debug('semantic_content_list: %s', semantic_content_list)
        assert len(semantic_content_list) == 1
        section = semantic_content_list[0]
        assert isinstance(section, SemanticSection)
        paragraphs = list(section.iter_by_type(SemanticParagraph))
        reference_citations = [
            citation
            for paragraph in paragraphs
            for citation in section.iter_by_type_recursively(SemanticReferenceCitation)
        ]
        assert len(reference_citations) == 1
        assert reference_citations[0].get_text() == 'Ref 1'

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

    def test_should_add_raw_figure_for_figure_text_to_section(self):
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
        assert section.get_text_by_type(SemanticRawFigure) == SECTION_PARAGRAPH_2

    def test_should_raw_table_for_table_text_to_section(self):
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
        assert section.get_text_by_type(SemanticRawTable) == SECTION_PARAGRAPH_2
