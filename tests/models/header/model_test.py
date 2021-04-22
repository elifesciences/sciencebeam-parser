from pygrobid.models.header.model import HeaderModel
from pygrobid.document.tei_document import TeiDocument


TITLE_1 = 'the title 1'
ABSTRACT_1 = 'the abstract 1'


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
