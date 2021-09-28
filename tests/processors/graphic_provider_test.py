from sciencebeam_parser.document.layout_document import (
    LayoutDocument,
    LayoutGraphic,
    LayoutPage
)
from sciencebeam_parser.processors.graphic_provider import (
    SimpleDocumentGraphicProvider
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
            local_file_path='/path/to/image.png'
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
            local_file_path='/path/to/image.png'
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
