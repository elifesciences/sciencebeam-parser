from sciencebeam_parser.utils.xml_writer import (
    parse_tag_expression
)


class TestParseTagExpression:
    def test_should_parse_simple_expression(self):
        tag_expression = parse_tag_expression('tag1')
        assert tag_expression.tag == 'tag1'
        assert tag_expression.attrib == {}

    def test_should_parse_simple_expression_with_attribute(self):
        tag_expression = parse_tag_expression('tag1[@attr1="value1"]')
        assert tag_expression.tag == 'tag1'
        assert tag_expression.attrib == {'attr1': 'value1'}
