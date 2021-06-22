from lxml.builder import E

from pygrobid.utils.xml import get_text_content


class TestGetTextContent:
    def test_should_return_text_of_simple_element(self):
        assert get_text_content(E.parent('text 1')) == 'text 1'
