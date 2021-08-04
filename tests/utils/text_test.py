from sciencebeam_parser.utils.text import normalize_text


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
