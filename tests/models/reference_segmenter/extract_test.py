import logging

from sciencebeam_parser.document.layout_document import LayoutBlock
from sciencebeam_parser.document.semantic_document import (
    SemanticHeading,
    SemanticLabel,
    SemanticRawReference,
    SemanticRawReferenceText
)
from sciencebeam_parser.models.reference_segmenter.extract import (
    ReferenceSegmenterSemanticExtractor
)


LOGGER = logging.getLogger(__name__)


LONG_REFERENCE_TEXT_1 = 'The title of the reference 1, 1991'


class TestReferenceSegmenterSemanticExtractor:
    def test_should_extract_single_raw_reference(self):
        semantic_content_list = list(
            ReferenceSegmenterSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<label>', LayoutBlock.for_text('1')),
                ('<reference>', LayoutBlock.for_text('Reference 1'))
            ])
        )
        assert len(semantic_content_list) == 1
        ref = semantic_content_list[0]
        assert isinstance(ref, SemanticRawReference)
        assert ref.view_by_type(SemanticLabel).get_text() == '1'
        assert ref.view_by_type(SemanticRawReferenceText).get_text() == 'Reference 1'

    def test_should_extract_multiple_raw_references(self):
        semantic_content_list = list(
            ReferenceSegmenterSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<label>', LayoutBlock.for_text('1')),
                ('<reference>', LayoutBlock.for_text('Reference 1')),
                ('<label>', LayoutBlock.for_text('2')),
                ('<reference>', LayoutBlock.for_text('Reference 2'))
            ])
        )
        assert len(semantic_content_list) == 2
        ref1 = semantic_content_list[0]
        assert isinstance(ref1, SemanticRawReference)
        assert ref1.view_by_type(SemanticLabel).get_text() == '1'
        assert ref1.view_by_type(SemanticRawReferenceText).get_text() == 'Reference 1'
        ref2 = semantic_content_list[1]
        assert isinstance(ref2, SemanticRawReference)
        assert ref2.view_by_type(SemanticLabel).get_text() == '2'
        assert ref2.view_by_type(SemanticRawReferenceText).get_text() == 'Reference 2'

    def test_should_treat_first_reference_without_label_as_heading(self):
        semantic_content_list = list(
            ReferenceSegmenterSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<reference>', LayoutBlock.for_text('References')),
                ('<label>', LayoutBlock.for_text('1')),
                ('<reference>', LayoutBlock.for_text('Reference 1')),
                ('<label>', LayoutBlock.for_text('2')),
                ('<reference>', LayoutBlock.for_text('Reference 2'))
            ])
        )
        assert len(semantic_content_list) == 3
        heading = semantic_content_list[0]
        assert isinstance(heading, SemanticHeading)
        assert heading.get_text() == 'References'
        ref1 = semantic_content_list[1]
        assert isinstance(ref1, SemanticRawReference)
        assert ref1.view_by_type(SemanticLabel).get_text() == '1'
        assert ref1.view_by_type(SemanticRawReferenceText).get_text() == 'Reference 1'
        ref2 = semantic_content_list[2]
        assert isinstance(ref2, SemanticRawReference)
        assert ref2.view_by_type(SemanticLabel).get_text() == '2'
        assert ref2.view_by_type(SemanticRawReferenceText).get_text() == 'Reference 2'

    def test_should_not_treat_long_first_reference_without_label_as_heading(self):
        semantic_content_list = list(
            ReferenceSegmenterSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<reference>', LayoutBlock.for_text(LONG_REFERENCE_TEXT_1)),
                ('<label>', LayoutBlock.for_text('1')),
                ('<reference>', LayoutBlock.for_text('Reference 1')),
                ('<label>', LayoutBlock.for_text('2')),
                ('<reference>', LayoutBlock.for_text('Reference 2'))
            ])
        )
        assert len(semantic_content_list) == 3
        ref1 = semantic_content_list[0]
        assert isinstance(ref1, SemanticRawReference)
        assert ref1.view_by_type(SemanticLabel).get_text() == ''
        assert ref1.view_by_type(SemanticRawReferenceText).get_text() == LONG_REFERENCE_TEXT_1

    def test_should_extract_note_around_multiple_raw_references(self):
        semantic_content_list = list(
            ReferenceSegmenterSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('O', LayoutBlock.for_text('Other 1')),
                ('<label>', LayoutBlock.for_text('1')),
                ('<reference>', LayoutBlock.for_text('Reference 1')),
                ('O', LayoutBlock.for_text('Other 2')),
                ('<label>', LayoutBlock.for_text('2')),
                ('<reference>', LayoutBlock.for_text('Reference 2')),
                ('O', LayoutBlock.for_text('Other 3'))
            ])
        )
        assert len(semantic_content_list) == 5
        assert semantic_content_list[0].get_text() == 'Other 1'
        ref1 = semantic_content_list[1]
        assert isinstance(ref1, SemanticRawReference)
        assert ref1.view_by_type(SemanticLabel).get_text() == '1'
        assert ref1.view_by_type(SemanticRawReferenceText).get_text() == 'Reference 1'
        assert semantic_content_list[2].get_text() == 'Other 2'
        ref2 = semantic_content_list[3]
        assert isinstance(ref2, SemanticRawReference)
        assert ref2.view_by_type(SemanticLabel).get_text() == '2'
        assert ref2.view_by_type(SemanticRawReferenceText).get_text() == 'Reference 2'
        assert semantic_content_list[4].get_text() == 'Other 3'
