from sciencebeam_parser.document.layout_document import (
    LayoutDocument,
    LayoutGraphic,
    LayoutPage,
    LayoutPageCoordinates
)
from sciencebeam_parser.processors.graphic_provider import (
    SimpleDocumentGraphicProvider
)


LAYOUT_PAGE_COORDINATES_1 = LayoutPageCoordinates(
    x=10, y=11, width=100, height=101, page_number=1
)


def _get_layout_document_for_layout_graphic(
    layout_graphic: LayoutGraphic
) -> LayoutDocument:
    return LayoutDocument(pages=[LayoutPage(
        blocks=[],
        graphics=[layout_graphic]
    )])


class TestSimpleDocumentGraphicProvider:
    def test_should_provide_semantic_graphic_with_assets(self):
        layout_graphic = LayoutGraphic(
            local_file_path='/path/to/image.png',
            coordinates=LAYOUT_PAGE_COORDINATES_1
        )
        semantic_graphic_list = list(
            SimpleDocumentGraphicProvider()
            .iter_semantic_graphic_for_layout_document(
                _get_layout_document_for_layout_graphic(layout_graphic),
                extract_graphic_assets=True
            )
        )
        assert len(semantic_graphic_list) == 1
        assert semantic_graphic_list[0].layout_graphic == layout_graphic
        assert semantic_graphic_list[0].relative_path == 'image.png'

    def test_should_provide_semantic_graphic_without_assets(self):
        layout_graphic = LayoutGraphic(
            local_file_path='/path/to/image.png',
            coordinates=LAYOUT_PAGE_COORDINATES_1
        )
        semantic_graphic_list = list(
            SimpleDocumentGraphicProvider()
            .iter_semantic_graphic_for_layout_document(
                _get_layout_document_for_layout_graphic(layout_graphic),
                extract_graphic_assets=False
            )
        )
        assert len(semantic_graphic_list) == 1
        assert semantic_graphic_list[0].layout_graphic == layout_graphic
        assert semantic_graphic_list[0].relative_path is None

    def test_should_ignore_layout_graphic_without_coordinates(self):
        layout_graphic = LayoutGraphic(
            local_file_path='/path/to/image.png',
            coordinates=None
        )
        semantic_graphic_list = list(
            SimpleDocumentGraphicProvider()
            .iter_semantic_graphic_for_layout_document(
                _get_layout_document_for_layout_graphic(layout_graphic),
                extract_graphic_assets=False
            )
        )
        assert not semantic_graphic_list
