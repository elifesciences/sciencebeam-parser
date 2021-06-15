"""
A semantically annotated document.
It doesn't have a specific structure as that depends on the output format (e.g. TEI).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional, Type, TypeVar, cast

from pygrobid.document.layout_document import LayoutBlock, LayoutToken


EMPTY_BLOCK = LayoutBlock(lines=[])


class SemanticContentWrapper(ABC):
    def get_text(self) -> str:
        return ' '.join((
            block.text
            for block in self.iter_blocks()
        ))

    def __len__(self) -> int:
        return len(list(self.iter_blocks()))

    @abstractmethod
    def iter_blocks(self) -> Iterable[LayoutBlock]:
        pass

    def iter_tokens(self) -> Iterable[LayoutToken]:
        return (
            token
            for block in self.iter_blocks()
            for token in block.iter_all_tokens()
        )

    @property
    def merged_block(self) -> LayoutBlock:
        return LayoutBlock.merge_blocks(self.iter_blocks())


@dataclass
class SemanticSimpleContentWrapper(SemanticContentWrapper):
    content: LayoutBlock = EMPTY_BLOCK

    def iter_blocks(self) -> Iterable[LayoutBlock]:
        return [self.content]

    def add_content(self, block: LayoutBlock):
        self.content = LayoutBlock(
            lines=self.content.lines + block.lines
        )


EMPTY_CONTENT = SemanticSimpleContentWrapper()


T_SemanticContentWrapper = TypeVar('T_SemanticContentWrapper', bound=SemanticContentWrapper)


@dataclass
class SemanticMixedContentWrapper(SemanticContentWrapper):
    mixed_content: List[SemanticContentWrapper] = field(default_factory=list)

    def __iter__(self) -> Iterator[SemanticContentWrapper]:
        return iter(self.mixed_content)

    def iter_blocks(self) -> Iterable[LayoutBlock]:
        return (
            block
            for content in self.mixed_content
            for block in content.iter_blocks()
        )

    def add_block_content(self, block: LayoutBlock):
        self.add_content(SemanticSimpleContentWrapper(block))

    def add_content(self, content: SemanticContentWrapper):
        assert not isinstance(content, LayoutBlock)
        self.mixed_content.append(content)

    def add_content_and_return_content(
        self, content: T_SemanticContentWrapper
    ) -> T_SemanticContentWrapper:
        self.add_content(content)
        return content

    def iter_by_type(
        self, type_: Type[T_SemanticContentWrapper]
    ) -> Iterable[T_SemanticContentWrapper]:
        return (
            content for content in self.mixed_content
            if isinstance(content, type_)
        )

    def view_by_type(self, type_: Type[T_SemanticContentWrapper]) -> 'SemanticMixedContentWrapper':
        return SemanticMixedContentWrapper(list(self.iter_by_type(type_)))

    def get_text_list(self) -> List[str]:
        return [content.get_text() for content in self.mixed_content]


@dataclass
class SemanticNote(SemanticSimpleContentWrapper):
    note_type: str = 'other'


@dataclass
class SemanticMeta:
    title: SemanticMixedContentWrapper = field(default_factory=SemanticMixedContentWrapper)
    abstract: SemanticMixedContentWrapper = field(default_factory=SemanticMixedContentWrapper)


class SemanticHeading(SemanticSimpleContentWrapper):
    pass


class SemanticParagraph(SemanticMixedContentWrapper):
    pass


class SemanticSectionTypes:
    ACKNOWLEDGEMENT = 'ACKNOWLEDGEMENT'
    OTHER = 'OTHER'


@dataclass
class SemanticSection(SemanticMixedContentWrapper):
    section_type: str = SemanticSectionTypes.OTHER

    @property
    def headings(self) -> List[SemanticHeading]:
        return list(self.iter_by_type(SemanticHeading))

    def get_heading_text(self) -> str:
        return '\n'.join(self.view_by_type(SemanticHeading).get_text_list())

    @property
    def paragraphs(self) -> List[SemanticParagraph]:
        return list(self.iter_by_type(SemanticParagraph))

    def get_paragraph_text_list(self) -> List[str]:
        return self.view_by_type(SemanticParagraph).get_text_list()

    def add_heading_block(self, block: LayoutBlock) -> SemanticHeading:
        return self.add_content_and_return_content(SemanticHeading(block))

    def add_new_paragraph(self) -> SemanticParagraph:
        return self.add_content_and_return_content(SemanticParagraph())

    def add_note(self, block: LayoutBlock, note_type: str) -> SemanticNote:
        return self.add_content_and_return_content(
            SemanticNote(block, note_type=note_type)
        )

    def get_notes(self, note_type: str) -> List[SemanticNote]:
        return [
            note
            for note in self.iter_by_type(SemanticNote)
            if note.note_type == note_type
        ]

    def get_notes_text_list(self, note_type: str) -> List[str]:
        return [note.get_text() for note in self.get_notes(note_type)]

    @property
    def sections(self) -> List['SemanticSection']:
        return list(self.iter_by_type(SemanticSection))

    def get_sections(
        self,
        section_type: Optional[str] = None
    ) -> List['SemanticSection']:
        return [
            section
            for section in self.iter_by_type(SemanticSection)
            if not section_type or section.section_type == section_type
        ]

    def view_by_section_type(self, section_type: str) -> 'SemanticMixedContentWrapper':
        return SemanticMixedContentWrapper(
            cast(List[SemanticContentWrapper], self.get_sections(section_type))
        )

    def add_new_section(
        self,
        section_type: str = SemanticSectionTypes.OTHER
    ) -> 'SemanticSection':
        return self.add_content_and_return_content(
            SemanticSection(section_type=section_type)
        )


@dataclass
class SemanticDocument:
    meta: SemanticMeta = field(default_factory=SemanticMeta)
    body_section: SemanticSection = field(default_factory=SemanticSection)
    back_section: SemanticSection = field(default_factory=SemanticSection)
