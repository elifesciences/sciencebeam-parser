from pygrobid.document.semantic_document import (
    SemanticAbstract,
    SemanticFront,
    SemanticRawAddress,
    SemanticRawAffiliation,
    SemanticTitle
)
from pygrobid.document.layout_document import (
    LOGGER,
    LayoutBlock,
    join_layout_tokens
)

from pygrobid.models.header.extract import (
    HeaderSemanticExtractor,
    get_cleaned_abstract_text,
    get_cleaned_abstract_layout_block
)


TITLE_1 = 'the title 1'
ABSTRACT_1 = 'the abstract 1'
AUTHOR_1 = 'Author 1'
AUTHOR_2 = 'Author 2'
AFFILIATION_1 = 'Affiliation 1'
ADDRESS_1 = 'Address 1'


class TestGetCleanedAbstractText:
    def test_should_return_none_if_passed_in_text_was_none(self):
        assert get_cleaned_abstract_text(None) is None

    def test_should_return_empty_str_if_passed_in_text_was_empty(self):
        assert get_cleaned_abstract_text('') == ''

    def test_should_return_abstract_if_it_doesnt_contain_prefix(self):
        assert get_cleaned_abstract_text(ABSTRACT_1) == ABSTRACT_1

    def test_should_return_remove_abstract_prefix(self):
        assert get_cleaned_abstract_text(
            'Abstract ' + ABSTRACT_1
        ) == ABSTRACT_1

    def test_should_return_remove_abstract_dot_prefix(self):
        assert get_cleaned_abstract_text(
            'Abstract. ' + ABSTRACT_1
        ) == ABSTRACT_1

    def test_should_return_remove_abstract_colon_prefix(self):
        assert get_cleaned_abstract_text(
            'Abstract: ' + ABSTRACT_1
        ) == ABSTRACT_1


class TestGetCleanedAbstractLayoutBlock:
    def test_should_return_none_if_passed_in_text_was_none(self):
        assert get_cleaned_abstract_layout_block(None) is None

    def test_should_return_empty_str_if_passed_in_text_was_empty(self):
        layout_block = LayoutBlock(lines=[])
        assert get_cleaned_abstract_layout_block(layout_block) == layout_block

    def test_should_return_abstract_if_it_doesnt_contain_prefix(self):
        layout_block = LayoutBlock.for_text(ABSTRACT_1)
        cleaned_layout_block = get_cleaned_abstract_layout_block(layout_block)
        assert join_layout_tokens(cleaned_layout_block.lines[0].tokens) == ABSTRACT_1

    def test_should_return_remove_abstract_prefix(self):
        layout_block = LayoutBlock.for_text('Abstract ' + ABSTRACT_1)
        cleaned_layout_block = get_cleaned_abstract_layout_block(layout_block)
        assert join_layout_tokens(cleaned_layout_block.lines[0].tokens) == ABSTRACT_1

    def test_should_return_remove_abstract_dot_prefix(self):
        layout_block = LayoutBlock.for_text('Abstract. ' + ABSTRACT_1)
        cleaned_layout_block = get_cleaned_abstract_layout_block(layout_block)
        assert join_layout_tokens(cleaned_layout_block.lines[0].tokens) == ABSTRACT_1

    def test_should_return_remove_abstract_colon_prefix(self):
        layout_block = LayoutBlock.for_text('Abstract: ' + ABSTRACT_1)
        cleaned_layout_block = get_cleaned_abstract_layout_block(layout_block)
        assert join_layout_tokens(cleaned_layout_block.lines[0].tokens) == ABSTRACT_1


class TestHeaderSemanticExtractor:
    def test_should_set_title_and_abstract(self):
        semantic_content_list = list(
            HeaderSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<title>', LayoutBlock.for_text(TITLE_1)),
                ('<abstract>', LayoutBlock.for_text(ABSTRACT_1))
            ])
        )
        front = SemanticFront(semantic_content_list)
        LOGGER.debug('front: %s', front)
        assert front.get_text_by_type(SemanticTitle) == TITLE_1
        assert front.get_text_by_type(SemanticAbstract) == ABSTRACT_1

    def test_should_ignore_additional_title_and_abstract(self):
        # Note: this behaviour should be reviewed
        semantic_content_list = list(
            HeaderSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<title>', LayoutBlock.for_text(TITLE_1)),
                ('<abstract>', LayoutBlock.for_text(ABSTRACT_1)),
                ('<title>', LayoutBlock.for_text('other')),
                ('<abstract>', LayoutBlock.for_text('other'))
            ])
        )
        front = SemanticFront(semantic_content_list)
        LOGGER.debug('front: %s', front)
        assert front.get_text_by_type(SemanticTitle) == TITLE_1
        assert front.get_text_by_type(SemanticAbstract) == ABSTRACT_1

    def test_should_add_raw_authors(self):
        semantic_content_list = list(
            HeaderSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<author>', LayoutBlock.for_text(AUTHOR_1))
            ])
        )
        front = SemanticFront(semantic_content_list)
        LOGGER.debug('front: %s', front)
        assert front.get_raw_authors_text() == AUTHOR_1

    def test_should_add_raw_affiliation_address(self):
        semantic_content_list = list(
            HeaderSemanticExtractor().iter_semantic_content_for_entity_blocks([
                ('<affiliation>', LayoutBlock.for_text(AFFILIATION_1)),
                ('<address>', LayoutBlock.for_text(ADDRESS_1))
            ])
        )
        front = SemanticFront(semantic_content_list)
        LOGGER.debug('front: %s', front)
        assert front.get_text_by_type(SemanticRawAffiliation) == AFFILIATION_1
        assert front.get_text_by_type(SemanticRawAddress) == ADDRESS_1
