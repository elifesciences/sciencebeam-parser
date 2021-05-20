from dataclasses import dataclass
from typing import List, Iterable, Optional, Tuple

from pygrobid.utils.tokenizer import get_tokenized_tokens


@dataclass
class LayoutFont:
    font_id: str
    font_family: Optional[str] = None
    font_size: Optional[float] = None
    is_bold: Optional[bool] = None
    is_italics: Optional[bool] = None


EMPTY_FONT = LayoutFont(font_id='_EMPTY')


@dataclass
class LayoutToken:
    text: str
    font: LayoutFont = EMPTY_FONT
    whitespace: str = ' '

    def retokenize(self) -> List['LayoutToken']:
        token_texts = get_tokenized_tokens(self.text, keep_whitespace=True)
        if token_texts == [self.text]:
            return [self]
        texts_with_whitespace: List[Tuple[str, str]] = []
        pending_token_text = ''
        pending_whitespace = ''
        for token_text in token_texts:
            if not token_text.strip():
                pending_whitespace += token_text
                continue
            if pending_token_text:
                texts_with_whitespace.append((pending_token_text, pending_whitespace))
            pending_token_text = token_text
            pending_whitespace = ''
        pending_whitespace += self.whitespace
        if pending_token_text:
            texts_with_whitespace.append((pending_token_text, pending_whitespace))
        return [
            LayoutToken(
                text=token_text,
                font=self.font,
                whitespace=whitespace
            )
            for token_text, whitespace in texts_with_whitespace
        ]


def join_layout_tokens(layout_tokens: List[LayoutToken]) -> str:
    return ''.join([
        (
            token.text + token.whitespace
            if index < len(layout_tokens) - 1
            else token.text
        )
        for index, token in enumerate(layout_tokens)
    ])


@dataclass
class LayoutLine:
    tokens: List[LayoutToken]

    def retokenize(self) -> 'LayoutLine':
        return LayoutLine(tokens=[
            tokenized_token
            for token in self.tokens
            for tokenized_token in token.retokenize()
        ])


@dataclass
class LayoutBlock:
    lines: List[LayoutLine]

    def retokenize(self) -> 'LayoutBlock':
        return LayoutBlock(lines=[
            line.retokenize()
            for line in self.lines
        ])

    def remove_empty_lines(self) -> 'LayoutBlock':
        return LayoutBlock(lines=[
            line
            for line in self.lines
            if line.tokens
        ])


@dataclass
class LayoutPage:
    blocks: List[LayoutBlock]

    def retokenize(self) -> 'LayoutPage':
        return LayoutPage(blocks=[
            block.retokenize()
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
            for line in block.lines
            for token in line.tokens
        )

    def retokenize(self) -> 'LayoutDocument':
        return LayoutDocument(pages=[
            page.retokenize()
            for page in self.pages
        ])

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


def retokenize_layout_document(layout_document: LayoutDocument) -> LayoutDocument:
    return layout_document.retokenize()


def remove_empty_blocks(layout_document: LayoutDocument) -> LayoutDocument:
    return layout_document.remove_empty_blocks()
