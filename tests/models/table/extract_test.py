import logging

from sciencebeam_parser.document.layout_document import LayoutBlock
from sciencebeam_parser.document.semantic_document import (
    SemanticCaption,
    SemanticLabel,
    SemanticTable
)
from sciencebeam_parser.models.table.extract import (
    TableSemanticExtractor
)


LOGGER = logging.getLogger(__name__)


class TestFableSemanticExtractor:
    def test_should_extract_single_figure(self):
        semantic_content_list = list(
            TableSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<label>', LayoutBlock.for_text('Table 1')),
                ('<figDesc>', LayoutBlock.for_text('Caption 1'))
            ])
        )
        assert len(semantic_content_list) == 1
        table = semantic_content_list[0]
        assert isinstance(table, SemanticTable)
        assert table.view_by_type(SemanticLabel).get_text() == 'Table 1'
        assert table.view_by_type(SemanticCaption).get_text() == 'Caption 1'
