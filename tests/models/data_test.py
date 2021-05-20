from pygrobid.document.layout_document import LayoutFont, LayoutToken
from pygrobid.models.data import (
    get_token_font_size_feature,
    get_digit_feature,
    get_capitalisation_feature,
    get_punctuation_profile_feature
)


class TestGetTokenFontSizeFeature:
    def test_should_return_higherfont_without_previous_token(self):
        assert get_token_font_size_feature(
            previous_token=None,
            current_token=LayoutToken('', font=LayoutFont(
                font_id='dummy'
            ))
        ) == 'HIGHERFONT'

    def test_should_return_lowerfont_if_font_size_is_smaller(self):
        assert get_token_font_size_feature(
            previous_token=LayoutToken('', font=LayoutFont(
                font_id='dummy', font_size=2
            )),
            current_token=LayoutToken('', font=LayoutFont(
                font_id='dummy', font_size=1
            ))
        ) == 'LOWERFONT'

    def test_should_return_samefont_if_font_size_is_the_same(self):
        assert get_token_font_size_feature(
            previous_token=LayoutToken('', font=LayoutFont(
                font_id='dummy', font_size=1
            )),
            current_token=LayoutToken('', font=LayoutFont(
                font_id='dummy', font_size=1
            ))
        ) == 'SAMEFONTSIZE'

    def test_should_return_higherfont_if_font_size_is_larger(self):
        assert get_token_font_size_feature(
            previous_token=LayoutToken('', font=LayoutFont(
                font_id='dummy', font_size=1
            )),
            current_token=LayoutToken('', font=LayoutFont(
                font_id='dummy', font_size=2
            ))
        ) == 'HIGHERFONT'

    def test_should_return_higherfont_if_previous_font_has_no_size(self):
        assert get_token_font_size_feature(
            previous_token=LayoutToken('', font=LayoutFont(
                font_id='dummy', font_size=None
            )),
            current_token=LayoutToken('', font=LayoutFont(
                font_id='dummy', font_size=1
            ))
        ) == 'HIGHERFONT'

    def test_should_return_higherfont_if_new_font_has_no_size(self):
        assert get_token_font_size_feature(
            previous_token=LayoutToken('', font=LayoutFont(
                font_id='dummy', font_size=1
            )),
            current_token=LayoutToken('', font=LayoutFont(
                font_id='dummy', font_size=None
            ))
        ) == 'HIGHERFONT'


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
