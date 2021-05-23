from pygrobid.models.header.model import (
    HeaderModel,
    get_cleaned_abstract_text
)
from pygrobid.document.tei_document import TeiDocument


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


class TestHeaderModel:
    def test_should_set_title_and_abstract(self):
        document = TeiDocument()
        header_model = HeaderModel('dummy-path')
        header_model.update_document_with_entity_values(
            document,
            [('<title>', TITLE_1), ('<abstract>', ABSTRACT_1)]
        )
        assert document.get_title() == TITLE_1
        assert document.get_abstract() == ABSTRACT_1

    def test_should_ignore_additional_title_and_abstract(self):
        document = TeiDocument()
        header_model = HeaderModel('dummy-path')
        header_model.update_document_with_entity_values(
            document,
            [
                ('<title>', TITLE_1), ('<abstract>', ABSTRACT_1),
                ('<title>', 'other'), ('<abstract>', 'other')
            ]
        )
        assert document.get_title() == TITLE_1
        assert document.get_abstract() == ABSTRACT_1
