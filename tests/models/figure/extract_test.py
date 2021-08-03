import logging

from sciencebeam_parser.document.layout_document import LayoutBlock
from sciencebeam_parser.document.semantic_document import (
    SemanticCaption,
    SemanticFigure,
    SemanticLabel
)
from sciencebeam_parser.models.figure.extract import (
    FigureSemanticExtractor
)


LOGGER = logging.getLogger(__name__)


class TestFigureSemanticExtractor:
    def test_should_extract_single_figure(self):
        semantic_content_list = list(
            FigureSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<label>', LayoutBlock.for_text('Figure 1')),
                ('<figDesc>', LayoutBlock.for_text('Caption 1'))
            ])
        )
        assert len(semantic_content_list) == 1
        figure = semantic_content_list[0]
        assert isinstance(figure, SemanticFigure)
        assert figure.view_by_type(SemanticLabel).get_text() == 'Figure 1'
        assert figure.view_by_type(SemanticCaption).get_text() == 'Caption 1'
