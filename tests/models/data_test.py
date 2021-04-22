from pygrobid.models.data import (
    get_digit_feature,
    get_capitalisation_feature,
    get_punctuation_profile_feature
)


class TestGetDigitFeature:
    def test_should_return_nodigit(self):
        assert get_digit_feature('abc') == 'NODIGIT'

    def test_should_return_alldigit(self):
        assert get_digit_feature('123') == 'ALLDIGIT'

    def test_should_return_containsdigit(self):
        assert get_digit_feature('abc123xyz') == 'CONTAINSDIGITS'


class TestGetCapitalisationFeature:
    def test_should_return_nocaps(self):
        assert get_capitalisation_feature('abc') == 'NOCAPS'

    def test_should_return_allcap(self):
        assert get_capitalisation_feature('ABC') == 'ALLCAP'

    def test_should_return_initcap(self):
        assert get_capitalisation_feature('Abc') == 'INITCAP'


class TestGetPunctuationProfileFeature:
    def test_should_return_openbracket(self):
        assert get_punctuation_profile_feature('(') == 'OPENBRACKET'
        assert get_punctuation_profile_feature('[') == 'OPENBRACKET'

    def test_should_return_endbracket(self):
        assert get_punctuation_profile_feature(')') == 'ENDBRACKET'
        assert get_punctuation_profile_feature(']') == 'ENDBRACKET'

    def test_should_return_dot(self):
        assert get_punctuation_profile_feature('.') == 'DOT'

    def test_should_return_comma(self):
        assert get_punctuation_profile_feature(',') == 'COMMA'

    def test_should_return_hyphen(self):
        assert get_punctuation_profile_feature('-') == 'HYPHEN'

    def test_should_return_quote(self):
        assert get_punctuation_profile_feature('"') == 'QUOTE'
        assert get_punctuation_profile_feature('\'') == 'QUOTE'
        assert get_punctuation_profile_feature('`') == 'QUOTE'

    def test_should_return_punct(self):
        assert get_punctuation_profile_feature(',,') == 'PUNCT'
        assert get_punctuation_profile_feature('::') == 'PUNCT'
        assert get_punctuation_profile_feature(';;') == 'PUNCT'
        assert get_punctuation_profile_feature('??') == 'PUNCT'
        assert get_punctuation_profile_feature('..') == 'PUNCT'

    def test_should_return_nopunct(self):
        assert get_punctuation_profile_feature('abc') == 'NOPUNCT'
