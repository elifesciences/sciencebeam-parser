import logging
from dataclasses import dataclass
from functools import partial
from typing import Callable, List, Iterable, NamedTuple, Optional, Tuple

from sciencebeam_parser.utils.tokenizer import iter_tokenized_tokens, get_tokenized_tokens


LOGGER = logging.getLogger(__name__)


class LayoutFont(NamedTuple):
    font_id: str
    font_family: Optional[str] = None
    font_size: Optional[float] = None
    is_bold: Optional[bool] = None
    is_italics: Optional[bool] = None
    is_subscript: Optional[bool] = None
    is_superscript: Optional[bool] = None


EMPTY_FONT = LayoutFont(font_id='_EMPTY')


class LayoutPageCoordinates(NamedTuple):
    x: float
    y: float
    width: float
    height: float
    page_number: int = 0

    def get_merged_with(
        self,
        other: 'LayoutPageCoordinates'
    ) -> 'LayoutPageCoordinates':
        assert self.page_number == other.page_number, \
            'cannot merge coordinates on different pages'
        x = min(self.x, other.x)
        y = min(self.y, other.y)
        width = max(self.x + self.width, other.x + other.width) - x
        height = max(self.y + self.height, other.y + other.height) - y
        return LayoutPageCoordinates(
            x=x, y=y, width=width, height=height, page_number=self.page_number
        )


def get_merged_coordinates_list(
    coordinates_list: Iterable[LayoutPageCoordinates]
) -> List[LayoutPageCoordinates]:
    result: List[LayoutPageCoordinates] = []
    pending_coordinates: Optional[LayoutPageCoordinates] = None
    for coordinates in coordinates_list:
        if not pending_coordinates:
            pending_coordinates = coordinates
            continue
        if coordinates.page_number != pending_coordinates.page_number:
            result.append(pending_coordinates)
            pending_coordinates = coordinates
            continue
        pending_coordinates = pending_coordinates.get_merged_with(
            coordinates
        )
    if pending_coordinates:
        result.append(pending_coordinates)
    return result


class LayoutToken(NamedTuple):
    text: str
    font: LayoutFont = EMPTY_FONT
    whitespace: str = ' '
    coordinates: Optional[LayoutPageCoordinates] = None


T_FlatMapLayoutTokensFn = Callable[[LayoutToken], List[LayoutToken]]


def default_get_tokenized_tokens_keep_whitespace(text: str) -> List[str]:
    return get_tokenized_tokens(text, keep_whitespace=True)


def get_relative_coordinates(
    coordinates: Optional[LayoutPageCoordinates],
    text: str,
    text_character_offset: int,
    total_text_length: int
) -> Optional[LayoutPageCoordinates]:
    if not coordinates:
        return None
    return LayoutPageCoordinates(
        page_number=coordinates.page_number,
        x=(
            coordinates.x
            + coordinates.width * text_character_offset / total_text_length
        ),
        y=coordinates.y,
        width=(
            coordinates.width
            * len(text) / total_text_length
        ),
        height=coordinates.height
    )


def retokenize_layout_token(
    layout_token: LayoutToken,
    tokenize_fn: Optional[Callable[[str], List[str]]] = None
) -> List[LayoutToken]:
    if not layout_token.text.strip():
        return []
    if tokenize_fn is None:
        tokenize_fn = default_get_tokenized_tokens_keep_whitespace
    token_texts = tokenize_fn(layout_token.text)
    if token_texts == [layout_token.text]:
        return [layout_token]
    total_text_length = sum(len(token_text) for token_text in token_texts)
    texts_with_whitespace: List[Tuple[str, str, int]] = []
    pending_token_text = ''
    pending_whitespace = ''
    text_character_offset = 0
    pending_text_character_offset = 0
    for token_text in token_texts:
        if not token_text.strip():
            pending_whitespace += token_text
            text_character_offset += len(token_text)
            continue
        if pending_token_text:
            texts_with_whitespace.append((
                pending_token_text,
                pending_whitespace,
                pending_text_character_offset
            ))
        pending_token_text = token_text
        pending_whitespace = ''
        pending_text_character_offset = text_character_offset
        text_character_offset += len(token_text)
    pending_whitespace += layout_token.whitespace
    if pending_token_text:
        texts_with_whitespace.append((
            pending_token_text,
            pending_whitespace,
            pending_text_character_offset
        ))
    return [
        LayoutToken(
            text=token_text,
            font=layout_token.font,
            whitespace=whitespace,
            coordinates=get_relative_coordinates(
                layout_token.coordinates,
                pending_token_text,
                text_character_offset,
                total_text_length
            )
        )
        for token_text, whitespace, text_character_offset in texts_with_whitespace
    ]


def iter_layout_tokens_for_text(
    text: str,
    tail_whitespace: str = ' ',
    **kwargs
) -> Iterable[LayoutToken]:
    pending_text = ''
    pending_whitespace = ' '
    for token_text in iter_tokenized_tokens(text, keep_whitespace=True):
        if not token_text.strip():
            pending_whitespace += token_text
            continue
        if pending_text:
            yield LayoutToken(pending_text, whitespace=pending_whitespace, **kwargs)
        pending_text = token_text
        pending_whitespace = ''
    if pending_text:
        pending_whitespace += tail_whitespace
        yield LayoutToken(pending_text, whitespace=pending_whitespace, **kwargs)


def get_layout_tokens_for_text(*args, **kwargs) -> List[LayoutToken]:
    return list(iter_layout_tokens_for_text(*args, **kwargs))


@dataclass
class LayoutLine:
    tokens: List[LayoutToken]

    @property
    def text(self) -> str:
        return join_layout_tokens(self.tokens)

    @staticmethod
    def for_text(text: str, **kwargs) -> 'LayoutLine':
        return LayoutLine(tokens=get_layout_tokens_for_text(text, **kwargs))

    def flat_map_layout_tokens(self, fn: T_FlatMapLayoutTokensFn) -> 'LayoutLine':
        return LayoutLine(tokens=[
            tokenized_token
            for token in self.tokens
            for tokenized_token in fn(token)
        ])


@dataclass
class LayoutBlock:
    lines: List[LayoutLine]

    def __len__(self):
        return len(self.lines)

    @staticmethod
    def for_tokens(tokens: List[LayoutToken]) -> 'LayoutBlock':
        if not tokens:
            return EMPTY_BLOCK
        return LayoutBlock(lines=[LayoutLine(tokens=tokens)])

    @staticmethod
    def merge_blocks(blocks: Iterable['LayoutBlock']) -> 'LayoutBlock':
        return LayoutBlock(lines=[
            line
            for block in blocks
            for line in block.lines
        ])

    @staticmethod
    def for_text(text: str, **kwargs) -> 'LayoutBlock':
        return LayoutBlock(lines=[LayoutLine.for_text(text, **kwargs)])

    def iter_all_tokens(self) -> Iterable[LayoutToken]:
        return (
            token
            for line in self.lines
            for token in line.tokens
        )

    def get_merged_coordinates_list(self) -> List[LayoutPageCoordinates]:
        return get_merged_coordinates_list([
            token.coordinates
            for token in self.iter_all_tokens()
            if token.coordinates
        ])

    def flat_map_layout_tokens(self, fn: T_FlatMapLayoutTokensFn) -> 'LayoutBlock':
        return LayoutBlock(lines=[
            line.flat_map_layout_tokens(fn)
            for line in self.lines
        ])

    def remove_empty_lines(self) -> 'LayoutBlock':
        return LayoutBlock(lines=[
            line
            for line in self.lines
            if line.tokens
        ])

    @property
    def text(self) -> str:
        return join_layout_tokens(self.iter_all_tokens())

    @property
    def whitespace(self) -> str:
        if not self.lines or not self.lines[-1].tokens:
            return ''
        return self.lines[-1].tokens[-1].whitespace


EMPTY_BLOCK = LayoutBlock(lines=[])


@dataclass
class LayoutPage:
    blocks: List[LayoutBlock]

    def flat_map_layout_tokens(self, fn: T_FlatMapLayoutTokensFn) -> 'LayoutPage':
        return LayoutPage(blocks=[
            block.flat_map_layout_tokens(fn)
            for block in self.blocks
        ])

    def remove_empty_blocks(self) -> 'LayoutPage':
        blocks: List[LayoutBlock] = [
            block.remove_empty_lines()
            for block in self.blocks
        ]
        return LayoutPage(blocks=[
            block
            for block in blocks
            if block.lines
        ])


@dataclass
class LayoutDocument:
    pages: List[LayoutPage]

    def __len__(self):
        return len(self.pages)

    @staticmethod
    def for_blocks(blocks: List[LayoutBlock]) -> 'LayoutDocument':
        return LayoutDocument(pages=[LayoutPage(blocks=blocks)])

    def iter_all_blocks(self) -> Iterable[LayoutBlock]:
        return (
            block
            for page in self.pages
            for block in page.blocks
        )

    def iter_all_tokens(self) -> Iterable[LayoutToken]:
        return (
            token
            for block in self.iter_all_blocks()
            for token in block.iter_all_tokens()
        )

    def flat_map_layout_tokens(
        self, fn: T_FlatMapLayoutTokensFn, **kwargs
    ) -> 'LayoutDocument':
        if kwargs:
            fn = partial(fn, **kwargs)
        return LayoutDocument(pages=[
            page.flat_map_layout_tokens(fn)
            for page in self.pages
        ])

    def retokenize(self, **kwargs) -> 'LayoutDocument':
        return self.flat_map_layout_tokens(retokenize_layout_token, **kwargs)

    def remove_empty_blocks(self) -> 'LayoutDocument':
        pages: List[LayoutPage] = [
            page.remove_empty_blocks()
            for page in self.pages
        ]
        return LayoutDocument(pages=[
            page
            for page in pages
            if page.blocks
        ])


class LayoutTokenIndexRange(NamedTuple):
    layout_token: LayoutToken
    start: int
    end: int


class LayoutTokensText:
    def __init__(self, layout_block: LayoutBlock) -> None:
        self.layout_block = layout_block
        text_fragments = []
        pending_whitespace = ''
        text_offset = 0
        token_index_ranges: List[LayoutTokenIndexRange] = []
        for line in layout_block.lines:
            for token in line.tokens:
                if pending_whitespace:
                    text_fragments.append(pending_whitespace)
                    text_offset += len(pending_whitespace)
                    pending_whitespace = ''
                token_text = token.text
                token_index_ranges.append(LayoutTokenIndexRange(
                    layout_token=token,
                    start=text_offset,
                    end=text_offset + len(token_text)
                ))
                text_fragments.append(token_text)
                text_offset += len(token_text)
                pending_whitespace += token.whitespace
        self.token_index_ranges = token_index_ranges
        self.text = ''.join(text_fragments)

    def __str__(self):
        return self.text

    def iter_layout_tokens_between(
        self, start: int, end: int
    ) -> Iterable[LayoutToken]:
        for token_index_range in self.token_index_ranges:
            if token_index_range.start >= end:
                break
            if token_index_range.end <= start:
                continue
            yield token_index_range.layout_token

    def get_layout_tokens_between(
        self, start: int, end: int
    ) -> List[LayoutToken]:
        return list(self.iter_layout_tokens_between(start, end))


def join_layout_tokens(layout_tokens: Iterable[LayoutToken]) -> str:
    layout_tokens = list(layout_tokens)
    return ''.join([
        (
            token.text + token.whitespace
            if index < len(layout_tokens) - 1
            else token.text
        )
        for index, token in enumerate(layout_tokens)
    ])


def flat_map_layout_document_tokens(
    layout_document: LayoutDocument,
    fn: T_FlatMapLayoutTokensFn,
    **kwargs
) -> LayoutDocument:
    return layout_document.flat_map_layout_tokens(fn, **kwargs)


def retokenize_layout_document(
    layout_document: LayoutDocument,
    **kwargs
) -> LayoutDocument:
    return layout_document.retokenize(**kwargs)


def remove_empty_blocks(layout_document: LayoutDocument) -> LayoutDocument:
    return layout_document.remove_empty_blocks()
