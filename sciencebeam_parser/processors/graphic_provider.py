import os
from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

from sciencebeam_parser.document.layout_document import LayoutDocument, LayoutGraphic
from sciencebeam_parser.document.semantic_document import SemanticGraphic


class DocumentGraphicProvider(ABC):
    @abstractmethod
    def iter_semantic_graphic_for_layout_document(
        self,
        layout_document: LayoutDocument,
        extract_graphic_assets: bool
    ) -> Iterable[SemanticGraphic]:
        pass


def get_semantic_graphic_for_layout_graphic(
    layout_graphic: LayoutGraphic,
    extract_graphic_assets: bool
) -> SemanticGraphic:
    relative_path: Optional[str] = None
    if layout_graphic.local_file_path and extract_graphic_assets:
        relative_path = os.path.basename(layout_graphic.local_file_path)
    return SemanticGraphic(
        layout_graphic=layout_graphic,
        relative_path=relative_path
    )


def get_semantic_graphic_list_for_layout_graphic_list(
    layout_graphic_iterable: Iterable[LayoutGraphic],
    extract_graphic_assets: bool
) -> List[SemanticGraphic]:
    return [
        get_semantic_graphic_for_layout_graphic(
            layout_graphic,
            extract_graphic_assets=extract_graphic_assets
        )
        for layout_graphic in layout_graphic_iterable
    ]


class SimpleDocumentGraphicProvider(DocumentGraphicProvider):
    def iter_semantic_graphic_for_layout_document(
        self,
        layout_document: LayoutDocument,
        extract_graphic_assets: bool
    ) -> Iterable[SemanticGraphic]:
        return get_semantic_graphic_list_for_layout_graphic_list(
            layout_document.iter_all_graphics(),
            extract_graphic_assets=extract_graphic_assets
        )
