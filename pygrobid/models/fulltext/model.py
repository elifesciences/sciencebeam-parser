import logging
from typing import Iterable, Optional, Tuple

from pygrobid.document.layout_document import (
    LayoutBlock
)
from pygrobid.document.semantic_document import (
    SemanticSection,
    SemanticParagraph,
    SemanticSectionTypes
)
from pygrobid.models.delft_model import DelftModel

from pygrobid.models.fulltext.data import FullTextDataGenerator


LOGGER = logging.getLogger(__name__)


class FullTextModel(DelftModel):
    def get_data_generator(self) -> FullTextDataGenerator:
        return FullTextDataGenerator()

    def update_section_with_entity_blocks(
        self,
        parent_section: SemanticSection,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        section_type: str = SemanticSectionTypes.OTHER
    ):
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        section: Optional[SemanticSection] = None
        paragraph: Optional[SemanticParagraph] = None
        _previous_tag: Optional[str] = None
        for name, layout_block in entity_tokens:
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug('entity_block: %r, %r', name, layout_block.text)
            previous_tag = _previous_tag
            _previous_tag = name
            if name in {'O', '<figure>', '<table>'}:
                LOGGER.debug('ignoring content (%r): %r', name, layout_block)
                note_type = 'other' if name == 'O' else name
                if section:
                    section.add_note(layout_block, note_type=note_type)
                else:
                    parent_section.add_note(layout_block, note_type=note_type)
                continue
            if name == '<section>':
                paragraph = None
                section = parent_section.add_new_section(section_type=section_type)
                section.add_heading_block(layout_block)
                continue
            # treat everything else as paragraph text
            if not section:
                section = parent_section.add_new_section(section_type=section_type)
            if (
                not paragraph
                or (
                    name == '<paragraph>'
                    and previous_tag == '<paragraph>'
                )
            ):
                paragraph = section.add_new_paragraph()
            paragraph.add_block_content(layout_block)

    def get_section_for_entity_blocks(
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]]
    ) -> SemanticSection:
        parent_section = SemanticSection()
        self.update_section_with_entity_blocks(parent_section, entity_tokens)
        return parent_section
