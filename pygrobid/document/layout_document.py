from dataclasses import dataclass
from typing import List, Iterable, Optional


@dataclass
class LayoutToken:
    text: Optional[str]


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
