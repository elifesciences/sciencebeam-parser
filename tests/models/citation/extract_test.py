import logging

from pygrobid.document.layout_document import LayoutBlock
from pygrobid.document.semantic_document import (
    SemanticMarker,
    SemanticRawAuthors,
    SemanticRawReference,
    SemanticRawReferenceText,
    SemanticReference,
    SemanticTitle
)
from pygrobid.models.citation.extract import CitationSemanticExtractor


LOGGER = logging.getLogger(__name__)


class TestReferenceSegmenterSemanticExtractor:
    def test_should_extract_single_raw_reference(self):
        semantic_content_list = list(
            CitationSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<author>', LayoutBlock.for_text('Author 1')),
                ('<title>', LayoutBlock.for_text('Title 1'))
            ])
        )
        assert len(semantic_content_list) == 1
        ref = semantic_content_list[0]
        assert isinstance(ref, SemanticReference)
        assert ref.view_by_type(SemanticRawAuthors).get_text() == 'Author 1'
        assert ref.view_by_type(SemanticTitle).get_text() == 'Title 1'
        assert ref.reference_id == 'b0'

    def test_should_add_raw_reference_semantic_content(self):
        semantic_marker = SemanticMarker(layout_block=LayoutBlock.for_text('1'))
        semantic_raw_ref_text = SemanticRawReferenceText(
            layout_block=LayoutBlock.for_text('Reference 1')
        )
        semantic_raw_ref = SemanticRawReference([
            semantic_marker, semantic_raw_ref_text
        ])
        semantic_raw_ref.reference_id = 'raw1'
        semantic_content_list = list(
            CitationSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<author>', LayoutBlock.for_text('Author 1')),
                ('<title>', LayoutBlock.for_text('Title 1'))
            ], semantic_raw_reference=semantic_raw_ref)
        )
        assert len(semantic_content_list) == 1
        ref = semantic_content_list[0]
        assert isinstance(ref, SemanticReference)
        assert ref.view_by_type(SemanticMarker).get_text() == semantic_marker.get_text()
        assert (
            ref.view_by_type(SemanticRawReferenceText).get_text()
            == semantic_raw_ref_text.get_text()
        )
        assert ref.view_by_type(SemanticRawAuthors).get_text() == 'Author 1'
        assert ref.view_by_type(SemanticTitle).get_text() == 'Title 1'
        assert ref.reference_id == semantic_raw_ref.reference_id
