from pygrobid.document.semantic_document import SemanticDocument
from pygrobid.document.layout_document import (
    LOGGER,
    LayoutBlock,
    join_layout_tokens
)

from pygrobid.models.header.model import (
    HeaderModel,
    get_cleaned_abstract_text,
    get_cleaned_abstract_layout_block
)


TITLE_1 = 'the title 1'
ABSTRACT_1 = 'the abstract 1'


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


class TestHeaderModel:
    def test_should_set_title_and_abstract(self):
        document = SemanticDocument()
        header_model = HeaderModel('dummy-path')
        header_model.update_semantic_document_with_entity_blocks(
            document,
            [
                ('<title>', LayoutBlock.for_text(TITLE_1)),
                ('<abstract>', LayoutBlock.for_text(ABSTRACT_1))
            ]
        )
        LOGGER.debug('document: %s', document)
        assert document.meta.title.get_text() == TITLE_1
        assert document.meta.abstract.get_text() == ABSTRACT_1

    def test_should_ignore_additional_title_and_abstract(self):
        # Note: this behaviour should be reviewed
        document = SemanticDocument()
        header_model = HeaderModel('dummy-path')
        header_model.update_semantic_document_with_entity_blocks(
            document,
            [
                ('<title>', LayoutBlock.for_text(TITLE_1)),
                ('<abstract>', LayoutBlock.for_text(ABSTRACT_1)),
                ('<title>', LayoutBlock.for_text('other')),
                ('<abstract>', LayoutBlock.for_text('other'))
            ]
        )
        LOGGER.debug('document: %s', document)
        assert document.meta.title.get_text() == TITLE_1
        assert document.meta.abstract.get_text() == ABSTRACT_1
