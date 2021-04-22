from dataclasses import dataclass
from typing import List, Iterable, Optional


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
    text: Optional[str]
    font: LayoutFont = EMPTY_FONT


@dataclass
class LayoutLine:
    tokens: List[LayoutToken]


@dataclass
class LayoutBlock:
    lines: List[LayoutLine]


@dataclass
class LayoutPage:
    blocks: List[LayoutBlock]


@dataclass
class LayoutDocument:
    pages: List[LayoutPage]

    def iter_all_blocks(self) -> Iterable[LayoutBlock]:
        return (
            block
            for page in self.pages
            for block in page.blocks
        )
