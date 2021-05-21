from pygrobid.utils.text import normalize_text


class TestNormalizeText:
    def test_should_replace_dash_with_hyphen(self):
        assert normalize_text('–') == '-'

    def test_should_replace_accent_with_quote(self):
        assert normalize_text('’') == "'"
