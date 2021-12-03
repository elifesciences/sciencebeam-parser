from lxml.builder import ElementMaker

from sciencebeam_parser.utils.xml import get_text_content_list
from sciencebeam_parser.utils.xml_writer import (
    XmlTreeWriter,
    parse_tag_expression
)


E = ElementMaker()


TEXT_1 = 'this is text 1'
TEXT_2 = 'this is text 2'


class TestParseTagExpression:
    def test_should_parse_simple_expression(self):
        tag_expression = parse_tag_expression('tag1')
        assert tag_expression.tag == 'tag1'
        assert tag_expression.attrib == {}

    def test_should_parse_simple_expression_with_attribute(self):
        tag_expression = parse_tag_expression('tag1[@attr1="value1"]')
        assert tag_expression.tag == 'tag1'
        assert tag_expression.attrib == {'attr1': 'value1'}


class TestXmlTreeWriter:
    def test_should_create_separate_elements_depending_on_path(self):
        xml_writer = XmlTreeWriter(E('root'), element_maker=E)
        xml_writer.require_path(['parent', 'child1'])
        xml_writer.append_text(TEXT_1)
        xml_writer.require_path(['parent', 'child2'])
        xml_writer.append_text(TEXT_2)
        root = xml_writer.root
        assert get_text_content_list(root.xpath('parent/child1')) == [TEXT_1]
        assert get_text_content_list(root.xpath('parent/child2')) == [TEXT_2]

    def test_should_create_use_same_element_for_same_path(self):
        xml_writer = XmlTreeWriter(E('root'), element_maker=E)
        xml_writer.require_path(['parent', 'child1'])
        xml_writer.append_text(TEXT_1)
        xml_writer.require_path(['parent', 'child1'])
        xml_writer.append_text(TEXT_2)
        root = xml_writer.root
        assert get_text_content_list(root.xpath('parent/child1')) == [TEXT_1 + TEXT_2]
