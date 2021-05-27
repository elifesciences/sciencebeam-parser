import logging
from typing import Iterable, Optional, Tuple

from pygrobid.document.layout_document import (
    LayoutBlock
)
from pygrobid.document.tei_document import TeiDocument, TeiSection, TeiSectionParagraph
from pygrobid.models.delft_model import DelftModel

from pygrobid.models.fulltext.data import FullTextDataGenerator


LOGGER = logging.getLogger(__name__)


class FullTextModel(DelftModel):
    def get_data_generator(self) -> FullTextDataGenerator:
        return FullTextDataGenerator()

    def update_document_with_entity_blocks(
        self,
        document: TeiDocument,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]]
    ):
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        section: Optional[TeiSection] = None
        paragraph: Optional[TeiSectionParagraph] = None
        _previous_tag: Optional[str] = None
        for name, layout_block in entity_tokens:
            previous_tag = _previous_tag
            _previous_tag = name
            if name in {'O', '<figure>', '<table>'}:
                LOGGER.debug('ignoring content (%r): %r', name, layout_block)
                note_type = 'other' if name == 'O' else name
                if section:
                    section.add_note(note_type, layout_block)
                else:
                    document.get_body().add_note(note_type, layout_block)
                continue
            if name == '<section>':
                if section:
                    if paragraph:
                        section.add_paragraph(paragraph)
                        paragraph = None
                    document.add_body_section(section)
                    section = None
                section = document.create_section()
                section.add_title(layout_block)
                continue
            # treat everything else as paragraph text
            if (
                paragraph
                and section
                and name == '<paragraph>'
                and previous_tag == '<paragraph>'
            ):
                section.add_paragraph(paragraph)
                paragraph = None
            if not section:
                section = document.create_section()
            if not paragraph:
                paragraph = section.create_paragraph()
            paragraph.add_content(layout_block)
        if section:
            if paragraph:
                section.add_paragraph(paragraph)
            document.add_body_section(section)
