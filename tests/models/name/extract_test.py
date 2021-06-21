import logging

from pygrobid.document.layout_document import LayoutBlock
from pygrobid.document.semantic_document import (
    SemanticAuthor,
    SemanticMarker,
    SemanticMiddleName,
    SemanticNameSuffix,
    SemanticNameTitle
)
from pygrobid.models.name.extract import NameSemanticExtractor


LOGGER = logging.getLogger(__name__)


class TestNameSemanticExtractor:
    def test_should_extract_single_author(self):
        semantic_content_list = list(
            NameSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<title>', LayoutBlock.for_text('Mr')),
                ('<forename>', LayoutBlock.for_text('John')),
                ('<middlename>', LayoutBlock.for_text('M')),
                ('<surname>', LayoutBlock.for_text('Smith')),
                ('<suffix>', LayoutBlock.for_text('Suffix1')),
                ('<marker>', LayoutBlock.for_text('1'))
            ])
        )
        assert len(semantic_content_list) == 1
        author = semantic_content_list[0]
        assert isinstance(author, SemanticAuthor)
        assert author.view_by_type(SemanticNameTitle).get_text() == 'Mr'
        assert author.given_name_text == 'John'
        assert author.view_by_type(SemanticMiddleName).get_text() == 'M'
        assert author.surname_text == 'Smith'
        assert author.view_by_type(SemanticNameSuffix).get_text() == 'Suffix1'
        assert author.view_by_type(SemanticMarker).get_text() == '1'

    def test_should_extract_multiple_authors(self):
        semantic_content_list = list(
            NameSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<forename>', LayoutBlock.for_text('John')),
                ('<surname>', LayoutBlock.for_text('Smith')),
                ('<marker>', LayoutBlock.for_text('1')),
                ('O', LayoutBlock.for_text(',')),
                ('<forename>', LayoutBlock.for_text('Maria')),
                ('<surname>', LayoutBlock.for_text('Madison')),
                ('<marker>', LayoutBlock.for_text('2'))
            ])
        )
        assert len(semantic_content_list) == 2
        author_1 = semantic_content_list[0]
        assert isinstance(author_1, SemanticAuthor)
        assert author_1.given_name_text == 'John'
        assert author_1.surname_text == 'Smith'
        assert author_1.view_by_type(SemanticMarker).get_text() == '1'
        author_2 = semantic_content_list[1]
        assert isinstance(author_2, SemanticAuthor)
        assert author_2.given_name_text == 'Maria'
        assert author_2.surname_text == 'Madison'
        assert author_2.view_by_type(SemanticMarker).get_text() == '2'

    def test_should_split_on_comma_before_marker(self):
        # The model currently does not provide segmentation as such
        # That is why the segmentation of authors is currently rule-based
        semantic_content_list = list(
            NameSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<marker>', LayoutBlock.for_text('1')),
                ('<forename>', LayoutBlock.for_text('John')),
                ('<surname>', LayoutBlock.for_text('Smith')),
                ('O', LayoutBlock.for_text(',')),
                ('<marker>', LayoutBlock.for_text('2')),
                ('<forename>', LayoutBlock.for_text('Maria')),
                ('<surname>', LayoutBlock.for_text('Madison')),
            ])
        )
        LOGGER.debug('semantic_content_list: %s', semantic_content_list)
        assert len(semantic_content_list) == 2
        author_1 = semantic_content_list[0]
        assert isinstance(author_1, SemanticAuthor)
        assert author_1.given_name_text == 'John'
        assert author_1.surname_text == 'Smith'
        assert author_1.view_by_type(SemanticMarker).get_text() == '1'
        author_2 = semantic_content_list[1]
        assert isinstance(author_2, SemanticAuthor)
        assert author_2.given_name_text == 'Maria'
        assert author_2.surname_text == 'Madison'
        assert author_2.view_by_type(SemanticMarker).get_text() == '2'

    def test_should_parse_multiple_markers(self):
        semantic_content_list = list(
            NameSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<forename>', LayoutBlock.for_text('John')),
                ('<surname>', LayoutBlock.for_text('Smith')),
                ('<marker>', LayoutBlock.for_text('1')),
                ('O', LayoutBlock.for_text(',')),
                ('<marker>', LayoutBlock.for_text('2')),
                ('O', LayoutBlock.for_text(',')),
                ('<forename>', LayoutBlock.for_text('Maria')),
                ('<surname>', LayoutBlock.for_text('Madison')),
                ('<marker>', LayoutBlock.for_text('2')),
                ('O', LayoutBlock.for_text(',')),
                ('<marker>', LayoutBlock.for_text('3')),
            ])
        )
        LOGGER.debug('semantic_content_list: %s', semantic_content_list)
        assert len(semantic_content_list) == 2
        author_1 = semantic_content_list[0]
        assert isinstance(author_1, SemanticAuthor)
        assert author_1.given_name_text == 'John'
        assert author_1.surname_text == 'Smith'
        assert author_1.view_by_type(SemanticMarker).get_text_list() == ['1', '2']
        author_2 = semantic_content_list[1]
        assert isinstance(author_2, SemanticAuthor)
        assert author_2.given_name_text == 'Maria'
        assert author_2.surname_text == 'Madison'
        assert author_2.view_by_type(SemanticMarker).get_text_list() == ['2', '3']
