import logging
from typing import Iterable, Mapping, Optional, Tuple

from pygrobid.document.semantic_document import (
    SemanticContentFactoryProtocol,
    SemanticContentWrapper,
    SemanticNote,
    SemanticParagraph,
    SemanticRawFigure,
    SemanticRawTable,
    SemanticSection,
    SemanticSectionTypes
)
from pygrobid.document.layout_document import LayoutBlock
from pygrobid.models.extract import ModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG: Mapping[str, SemanticContentFactoryProtocol] = {
    '<figure>': SemanticRawFigure,
    '<table>': SemanticRawTable
}


class FullTextSemanticExtractor(ModelSemanticExtractor):
    def get_semantic_content_for_entity_name(  # pylint: disable=too-many-return-statements
        self,
        name: str,
        layout_block: LayoutBlock
    ) -> SemanticContentWrapper:
        semantic_content_class = SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG.get(name)
        if semantic_content_class:
            return semantic_content_class(layout_block=layout_block)
        return SemanticNote(
            layout_block=layout_block,
            note_type=name
        )

    def iter_semantic_content_for_entity_blocks(  # pylint: disable=arguments-differ
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        section_type: str = SemanticSectionTypes.OTHER,
        **kwargs
    ) -> Iterable[SemanticContentWrapper]:
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
            if name in {'O'}:
                LOGGER.debug('ignoring content (%r): %r', name, layout_block)
                note_type = 'other' if name == 'O' else name
                if section:
                    section.add_note(layout_block, note_type=note_type)
                else:
                    yield SemanticNote(
                        layout_block=layout_block,
                        note_type=note_type
                    )
                continue
            if name == '<section>':
                paragraph = None
                if section:
                    yield section
                section = SemanticSection(section_type=section_type)
                section.add_heading_block(layout_block)
                continue
            if not section:
                section = SemanticSection(section_type=section_type)
            if name in SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG.keys():
                section.add_content(self.get_semantic_content_for_entity_name(
                    name, layout_block=layout_block
                ))
                continue
            # treat everything else as paragraph text
            if (
                not paragraph
                or (
                    name == '<paragraph>'
                    and previous_tag == '<paragraph>'
                )
            ):
                paragraph = section.add_new_paragraph()
            paragraph.add_block_content(layout_block)
        if section:
            yield section
