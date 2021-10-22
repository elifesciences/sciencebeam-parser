from sciencebeam_parser.document.tei.common import TEI_E, TeiElementWrapper, format_coordinates
from sciencebeam_parser.document.layout_document import (
    LayoutGraphic,
    LayoutPageCoordinates
)
from sciencebeam_parser.document.semantic_document import (
    SemanticGraphic
)
from sciencebeam_parser.document.tei.factories import (
    DEFAULT_TEI_ELEMENT_FACTORY_CONTEXT
)
from sciencebeam_parser.document.tei.graphic import (
    GraphicTeiElementFactory
)


COORDINATES_1 = LayoutPageCoordinates(
    x=10,
    y=100,
    width=200,
    height=100,
    page_number=1
)


def _get_wrapped_graphic_tei_element(
    semantic_graphic: SemanticGraphic
) -> TeiElementWrapper:
    return TeiElementWrapper(TEI_E(
        'root',
        *GraphicTeiElementFactory().get_tei_children_for_semantic_content(
            semantic_graphic,
            context=DEFAULT_TEI_ELEMENT_FACTORY_CONTEXT
        )
    ))


class TestGraphicTeiElementFactory:
    def test_should_render_graphic_element_with_coords(self):
        semantic_graphic = SemanticGraphic(
            layout_graphic=LayoutGraphic(
                local_file_path='image1.png',
                coordinates=COORDINATES_1,
                graphic_type='svg'
            )
        )
        result = _get_wrapped_graphic_tei_element(semantic_graphic)
        graphic_elements = result.xpath_nodes(
            '//tei:graphic'
        )
        assert len(graphic_elements) == 1
        graphic_element = graphic_elements[0]
        assert graphic_element.attrib.get('coords') == format_coordinates(
            COORDINATES_1
        )
        assert graphic_element.attrib.get('type') == 'svg'
        assert not graphic_element.attrib.get('url')

    def test_should_render_graphic_element_with_url(self):
        semantic_graphic = SemanticGraphic(
            relative_path='rel-image1.png',
            layout_graphic=LayoutGraphic(
                local_file_path='image1.png',
                graphic_type='svg'
            )
        )
        result = _get_wrapped_graphic_tei_element(semantic_graphic)
        graphic_elements = result.xpath_nodes(
            '//tei:graphic'
        )
        assert len(graphic_elements) == 1
        graphic_element = graphic_elements[0]
        assert graphic_element.attrib.get('url') == 'rel-image1.png'
