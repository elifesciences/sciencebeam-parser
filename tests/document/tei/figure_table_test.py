from sciencebeam_parser.document.tei.common import TEI_E, TeiElementWrapper
from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutGraphic
)
from sciencebeam_parser.document.semantic_document import (
    SemanticCaption,
    SemanticFigure,
    SemanticGraphic,
    SemanticLabel
)
from sciencebeam_parser.document.tei.factories import (
    DEFAULT_TEI_ELEMENT_FACTORY_CONTEXT
)
from sciencebeam_parser.document.tei.figure_table import (
    FigureTeiElementFactory
)


FIGURE_XPATH = '//tei:figure[not(contains(@type, "table"))]'


def _get_wrapped_figure_tei_element(
    semantic_figure: SemanticFigure
) -> TeiElementWrapper:
    return TeiElementWrapper(TEI_E(
        'root',
        *FigureTeiElementFactory().get_tei_children_for_semantic_content(
            semantic_figure,
            context=DEFAULT_TEI_ELEMENT_FACTORY_CONTEXT
        )
    ))


class TestFigureTeiElementFactory:
    def test_should_render_label_description_and_id(self):
        semantic_figure = SemanticFigure([
            SemanticLabel(layout_block=LayoutBlock.for_text('Label 1')),
            SemanticCaption(layout_block=LayoutBlock.for_text('Caption 1'))
        ], content_id='fig_0')
        result = _get_wrapped_figure_tei_element(semantic_figure)
        assert result.get_xpath_text_content_list(
            f'{FIGURE_XPATH}/tei:head'
        ) == ['Label 1']
        assert result.get_xpath_text_content_list(
            f'{FIGURE_XPATH}/tei:label'
        ) == ['Label 1']
        assert result.get_xpath_text_content_list(
            f'{FIGURE_XPATH}/tei:figDesc'
        ) == ['Caption 1']
        assert result.get_xpath_text_content_list(
            f'{FIGURE_XPATH}/@xml:id'
        ) == ['fig_0']

    def test_should_render_graphic_element(self):
        semantic_figure = SemanticFigure([
            SemanticLabel(layout_block=LayoutBlock.for_text('Label 1')),
            SemanticCaption(layout_block=LayoutBlock.for_text('Caption 1')),
            SemanticGraphic(
                layout_graphic=LayoutGraphic(path='image1.png')
            )
        ], content_id='fig_0')
        result = _get_wrapped_figure_tei_element(semantic_figure)
        assert result.get_xpath_text_content_list(
            f'{FIGURE_XPATH}/tei:graphic'
        )
