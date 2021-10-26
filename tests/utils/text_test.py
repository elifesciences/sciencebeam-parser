from sciencebeam_parser.utils.text import normalize_text, parse_comma_separated_value


class TestNormalizeText:
    def test_should_replace_dash_with_hyphen(self):
        assert normalize_text('–') == '-'

    def test_should_replace_accent_with_quote(self):
        assert normalize_text('’') == "'"

    def test_should_normalize_multiple_spaces_to_one(self):
        assert normalize_text('a   b') == 'a b'

    def test_should_preserve_single_line_feed(self):
        assert normalize_text('a\nb') == 'a\nb'

    def test_should_remove_space_around_line_feed(self):
        assert normalize_text('a  \n  b') == 'a\nb'


class TestParseCommaSeparatedValue:
    def test_should_return_empty_list_for_empty_string(self):
        assert parse_comma_separated_value('') == []

    def test_should_return_empty_list_for_blank_string(self):
        assert parse_comma_separated_value('  ') == []

    def test_should_parse_single_value(self):
        assert parse_comma_separated_value('one') == ['one']

    def test_should_parse_multiple_values(self):
        assert parse_comma_separated_value('one,two,three') == ['one', 'two', 'three']

    def test_should_remove_spaces(self):
        assert parse_comma_separated_value(' one , two , three ') == ['one', 'two', 'three']
