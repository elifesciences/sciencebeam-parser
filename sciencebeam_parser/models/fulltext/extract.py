import logging
import re
from typing import Iterable, Mapping, Optional, Tuple

from sciencebeam_parser.document.semantic_document import (
    SemanticContentFactoryProtocol,
    SemanticContentWrapper,
    SemanticFigureCitation,
    SemanticHeading,
    SemanticLabel,
    SemanticNote,
    SemanticParagraph,
    SemanticRawEquation,
    SemanticRawEquationContent,
    SemanticRawFigure,
    SemanticRawTable,
    SemanticReferenceCitation,
    SemanticSection,
    SemanticSectionTypes,
    SemanticTableCitation,
    SemanticTitle
)
from sciencebeam_parser.document.layout_document import LayoutBlock, LayoutTokensText
from sciencebeam_parser.models.extract import SimpleModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG: Mapping[str, SemanticContentFactoryProtocol] = {
    '<figure>': SemanticRawFigure,
    '<table>': SemanticRawTable
}


PARAGRAPH_SEMANTIC_CONTENT_CLASS_BY_TAG: Mapping[str, SemanticContentFactoryProtocol] = {
    '<figure_marker>': SemanticFigureCitation,
    '<table_marker>': SemanticTableCitation,
    '<citation_marker>': SemanticReferenceCitation
}


HEADER_LABEL_REGEX = r'(\d+\.?(?:\d+\.?)*)\s*(\D.*)'


def get_section_label_and_title_from_layout_block(
    layout_block: LayoutBlock
) -> Tuple[Optional[LayoutBlock], LayoutBlock]:
    if not layout_block:
        return None, layout_block
    layout_tokens_text = LayoutTokensText(layout_block)
    text = str(layout_tokens_text)
    m = re.match(HEADER_LABEL_REGEX, text, re.IGNORECASE)
    if not m:
        return None, layout_block
    label_end = m.end(1)
    title_start = m.start(2)
    LOGGER.debug('label_end: %d, title_start: %d (text: %r)', label_end, title_start, text)
    section_label_layout_block = LayoutBlock.for_tokens(list(
        layout_tokens_text.iter_layout_tokens_between(0, label_end)
    ))
    section_title_layout_block = LayoutBlock.for_tokens(list(
        layout_tokens_text.iter_layout_tokens_between(title_start, len(text))
    ))
    return section_label_layout_block, section_title_layout_block


class FullTextSemanticExtractor(SimpleModelSemanticExtractor):
    def __init__(self):
        super().__init__(semantic_content_class_by_tag=SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG)

    def add_paragraph_content(
        self,
        paragraph: SemanticParagraph,
        name: str,
        layout_block: LayoutBlock
    ):
        semantic_content_class = PARAGRAPH_SEMANTIC_CONTENT_CLASS_BY_TAG.get(name)
        if semantic_content_class:
            paragraph.add_content(semantic_content_class(layout_block=layout_block))
            return
        paragraph.add_block_content(layout_block)

    def get_semantic_heading(self, layout_block: LayoutBlock):
        section_label_layout_block, section_title_layout_block = (
            get_section_label_and_title_from_layout_block(layout_block)
        )
        if section_label_layout_block:
            return SemanticHeading([
                SemanticLabel(layout_block=section_label_layout_block),
                SemanticTitle(layout_block=section_title_layout_block)
            ])
        return SemanticHeading([
            SemanticTitle(layout_block=section_title_layout_block)
        ])

    def get_raw_equation_child_semantic_content(
        self,
        name: str,
        layout_block: LayoutBlock
    ):
        if name == '<equation_label>':
            return SemanticLabel(layout_block=layout_block)
        if name == '<equation>':
            return SemanticRawEquationContent(layout_block=layout_block)
        return self.get_semantic_content_for_entity_name(
            name, layout_block=layout_block
        )

    def iter_semantic_content_for_entity_blocks(  # noqa pylint: disable=arguments-differ, too-many-branches
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        section_type: str = SemanticSectionTypes.OTHER,
        **kwargs
    ) -> Iterable[SemanticContentWrapper]:
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        section: Optional[SemanticSection] = None
        paragraph: Optional[SemanticParagraph] = None
        raw_equation: Optional[SemanticRawEquation] = None
        _previous_tag: Optional[str] = None
        for name, layout_block in entity_tokens:
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug('entity_block: %r, %r', name, layout_block.text)
            previous_tag = _previous_tag
            _previous_tag = name
            if name in {'O'}:
                LOGGER.debug('ignoring content (%r): %r', name, layout_block)
                note_type = 'fulltext:other' if name == 'O' else name
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
                raw_equation = None
                if section:
                    yield section
                section = SemanticSection(section_type=section_type)
                section.add_content(self.get_semantic_heading(layout_block))
                continue
            if not section:
                section = SemanticSection(section_type=section_type)
            if name in SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG:
                section.add_content(self.get_semantic_content_for_entity_name(
                    name, layout_block=layout_block
                ))
                continue
            # treat everything else as paragraph content
            if (
                not paragraph
                or (
                    name == '<paragraph>'
                    and previous_tag == '<paragraph>'
                )
            ):
                paragraph = section.add_new_paragraph()
            if name in {'<equation>', '<equation_label>'}:
                semantic_content = self.get_raw_equation_child_semantic_content(
                    name, layout_block=layout_block
                )
                if (
                    isinstance(semantic_content, SemanticRawEquationContent)
                    and raw_equation
                    and raw_equation.has_type(SemanticRawEquationContent)
                ):
                    LOGGER.debug('already has equation content, start new one')
                    raw_equation = None
                if not raw_equation:
                    raw_equation = SemanticRawEquation()
                    paragraph.add_content(raw_equation)
                raw_equation.add_content(semantic_content)
                continue
            raw_equation = None
            self.add_paragraph_content(
                paragraph, name, layout_block
            )
        if section:
            yield section
