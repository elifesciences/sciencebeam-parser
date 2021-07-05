"""
A semantically annotated document.
It doesn't have a specific structure as that depends on the output format (e.g. TEI).
"""
import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, List, Optional, Sequence, Type, TypeVar, cast
from typing_extensions import Protocol

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

    layout_block: dataclasses.InitVar[LayoutBlock] = None

    def __post_init__(self, layout_block: Optional[LayoutBlock] = None):
        if layout_block is not None:
            self.add_content(layout_block)

    def iter_blocks(self) -> Iterable[LayoutBlock]:
        return [self.content]

    def add_content(self, block: LayoutBlock):
        self.content = LayoutBlock(
            lines=self.content.lines + block.lines
        )


class SemanticContentFactoryProtocol(Protocol):
    def __call__(self, layout_block: LayoutBlock) -> SemanticContentWrapper:
        pass


EMPTY_CONTENT = SemanticSimpleContentWrapper()


T_SemanticContentWrapper = TypeVar('T_SemanticContentWrapper', bound=SemanticContentWrapper)


@dataclass
class SemanticMixedContentWrapper(SemanticContentWrapper):
    mixed_content: List[SemanticContentWrapper] = field(default_factory=list)
    layout_block: dataclasses.InitVar[LayoutBlock] = None

    def __post_init__(self, layout_block: Optional[LayoutBlock] = None):
        if layout_block is not None:
            self.add_block_content(layout_block)

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

    def flat_map_inplace(
        self,
        fn: Callable[[SemanticContentWrapper], Sequence[SemanticContentWrapper]]
    ):
        self.mixed_content = [
            replaced_content
            for content in self.mixed_content
            for replaced_content in fn(content)
        ]

    def flat_map_inplace_by_type(
        self,
        type_: Type[T_SemanticContentWrapper],
        fn: Callable[[SemanticContentWrapper], Sequence[SemanticContentWrapper]]
    ):
        self.flat_map_inplace(
            lambda content: (
                fn(content) if isinstance(content, type_)
                else [content]
            )
        )

    def get_text_list(self) -> List[str]:
        return [content.get_text() for content in self.mixed_content]

    def get_text_by_type(self, type_: Type[T_SemanticContentWrapper]) -> str:
        return self.view_by_type(type_).get_text()


@dataclass
class SemanticNote(SemanticSimpleContentWrapper):
    note_type: str = 'other'


class SemanticHeading(SemanticSimpleContentWrapper):
    pass


class SemanticParagraph(SemanticMixedContentWrapper):
    pass


class SemanticSectionTypes:
    ACKNOWLEDGEMENT = 'ACKNOWLEDGEMENT'
    OTHER = 'OTHER'


class SemanticLabel(SemanticSimpleContentWrapper):
    pass


class SemanticTitle(SemanticSimpleContentWrapper):
    pass


class SemanticJournal(SemanticSimpleContentWrapper):
    pass


class SemanticVolume(SemanticSimpleContentWrapper):
    pass


class SemanticIssue(SemanticSimpleContentWrapper):
    pass


@dataclass
class SemanticPageRange(SemanticSimpleContentWrapper):
    from_page: Optional[str] = None
    to_page: Optional[str] = None


class SemanticPublisher(SemanticSimpleContentWrapper):
    pass


class SemanticLocation(SemanticSimpleContentWrapper):
    pass


@dataclass
class SemanticDate(SemanticSimpleContentWrapper):
    year: Optional[int] = None


class SemanticExternalIdentifierTypes:
    ARXIV = 'ARXIV'
    DOI = 'DOI'
    PII = 'PII'
    PMCID = 'PMCID'
    PMID = 'PMID'


@dataclass
class SemanticExternalIdentifier(SemanticSimpleContentWrapper):
    value: Optional[str] = None
    external_identifier_type: Optional[str] = None


@dataclass
class SemanticExternalUrl(SemanticSimpleContentWrapper):
    value: Optional[str] = None


class SemanticAbstract(SemanticSimpleContentWrapper):
    pass


class SemanticRawNameList(SemanticMixedContentWrapper):
    pass


T_SemanticRawNameList = TypeVar('T_SemanticRawNameList', bound=SemanticRawNameList)


class SemanticRawAuthors(SemanticRawNameList):
    pass


class SemanticRawEditors(SemanticRawNameList):
    pass


class SemanticRawAffiliation(SemanticMixedContentWrapper):
    pass


class SemanticRawAddress(SemanticMixedContentWrapper):
    pass


class SemanticMarker(SemanticSimpleContentWrapper):
    pass


class SemanticNameTitle(SemanticMixedContentWrapper):
    pass


class SemanticNameSuffix(SemanticMixedContentWrapper):
    pass


class SemanticGivenName(SemanticMixedContentWrapper):
    pass


class SemanticMiddleName(SemanticMixedContentWrapper):
    pass


class SemanticSurname(SemanticMixedContentWrapper):
    pass


class SemanticName(SemanticMixedContentWrapper):
    @property
    def label_text(self) -> str:
        return self.view_by_type(SemanticLabel).get_text()

    @property
    def given_name_text(self) -> str:
        return self.view_by_type(SemanticGivenName).get_text()

    @property
    def surname_text(self) -> str:
        return self.view_by_type(SemanticSurname).get_text()


T_SemanticName = TypeVar('T_SemanticName', bound=SemanticName)


class SemanticAuthor(SemanticName):
    pass


class SemanticEditor(SemanticName):
    pass


class SemanticInstitution(SemanticMixedContentWrapper):
    pass


class SemanticDepartment(SemanticMixedContentWrapper):
    pass


class SemanticLaboratory(SemanticMixedContentWrapper):
    pass


class SemanticAddressField(SemanticMixedContentWrapper):
    pass


class SemanticAddressLine(SemanticAddressField):
    pass


class SemanticPostCode(SemanticAddressField):
    pass


class SemanticPostBox(SemanticAddressField):
    pass


class SemanticRegion(SemanticAddressField):
    pass


class SemanticSettlement(SemanticAddressField):
    pass


class SemanticCountry(SemanticAddressField):
    pass


class SemanticAffiliationAddress(SemanticMixedContentWrapper):
    affiliation_id: str = ''


class SemanticRawReferenceText(SemanticMixedContentWrapper):
    pass


class SemanticRawReference(SemanticMixedContentWrapper):
    reference_id: str = ''


class SemanticReference(SemanticMixedContentWrapper):
    reference_id: str = ''


class SemanticReferenceList(SemanticMixedContentWrapper):
    pass


class SemanticFront(SemanticMixedContentWrapper):
    @property
    def authors(self) -> List[SemanticAuthor]:
        return list(self.iter_by_type(SemanticAuthor))

    def get_raw_authors_text(self) -> str:
        return '\n'.join(self.view_by_type(SemanticRawAuthors).get_text_list())

    def get_authors_text(self) -> str:
        return '\n'.join(self.view_by_type(SemanticAuthor).get_text_list())


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
    front: SemanticFront = field(default_factory=SemanticFront)
    body_section: SemanticSection = field(default_factory=SemanticSection)
    back_section: SemanticSection = field(default_factory=SemanticSection)
