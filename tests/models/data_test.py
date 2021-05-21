from pygrobid.document.layout_document import LayoutCoordinates, LayoutFont, LayoutToken
from pygrobid.models.data import (
    RelativeFontSizeFeature,
    LineIndentationStatusFeature,
    get_token_font_size_feature,
    get_digit_feature,
    get_capitalisation_feature,
    get_punctuation_profile_feature
)


class TestRelativeFontSizeFeature:
    def test_should_return_is_smallest_largest_and_larger_than_avg(self):
        layout_tokens = [
            LayoutToken('', font=LayoutFont('font1', font_size=1)),
            LayoutToken('', font=LayoutFont('font2', font_size=2)),
            LayoutToken('', font=LayoutFont('font3', font_size=3)),
            LayoutToken('', font=LayoutFont('font4', font_size=4))
        ]
        relative_font_size_feature = RelativeFontSizeFeature(layout_tokens)
        assert [
            relative_font_size_feature.is_smallest_font_size(layout_token)
            for layout_token in layout_tokens
        ] == [True, False, False, False]
        assert [
            relative_font_size_feature.is_largest_font_size(layout_token)
            for layout_token in layout_tokens
        ] == [False, False, False, True]
        assert [
            relative_font_size_feature.is_larger_than_average_font_size(layout_token)
            for layout_token in layout_tokens
        ] == [False, False, True, True]

    def test_should_return_false_if_no_font_size_available(self):
        layout_tokens = [
            LayoutToken('', font=LayoutFont('font1', font_size=None)),
            LayoutToken('', font=LayoutFont('font2', font_size=None)),
            LayoutToken('', font=LayoutFont('font3', font_size=None)),
            LayoutToken('', font=LayoutFont('font4', font_size=None))
        ]
        relative_font_size_feature = RelativeFontSizeFeature(layout_tokens)
        assert [
            relative_font_size_feature.is_smallest_font_size(layout_token)
            for layout_token in layout_tokens
        ] == [False, False, False, False]
        assert [
            relative_font_size_feature.is_largest_font_size(layout_token)
            for layout_token in layout_tokens
        ] == [False, False, False, False]
        assert [
            relative_font_size_feature.is_larger_than_average_font_size(layout_token)
            for layout_token in layout_tokens
        ] == [False, False, False, False]


class TestLineIndentationStatusFeature:
    def test_(self):
        line_indentation_status_feature = LineIndentationStatusFeature()
        line_indentation_status_feature.on_new_line()
        assert line_indentation_status_feature.get_is_indented_and_update(
            LayoutToken('x', coordinates=LayoutCoordinates(x=10, y=10, width=10, height=10))
        ) is False
        line_indentation_status_feature.on_new_line()
        assert line_indentation_status_feature.get_is_indented_and_update(
            LayoutToken('x', coordinates=LayoutCoordinates(x=50, y=10, width=10, height=10))
        ) is True


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

    def test_should_return_allcap_for_symbols(self):
        assert get_capitalisation_feature('*') == 'ALLCAP'


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
        assert get_punctuation_profile_feature('–') == 'HYPHEN'

    def test_should_return_quote(self):
        assert get_punctuation_profile_feature('"') == 'QUOTE'
        assert get_punctuation_profile_feature('\'') == 'QUOTE'
        assert get_punctuation_profile_feature('`') == 'QUOTE'
        assert get_punctuation_profile_feature('’') == 'QUOTE'

    def test_should_return_punct(self):
        assert get_punctuation_profile_feature(',,') == 'PUNCT'
        assert get_punctuation_profile_feature('::') == 'PUNCT'
        assert get_punctuation_profile_feature(';;') == 'PUNCT'
        assert get_punctuation_profile_feature('??') == 'PUNCT'
        assert get_punctuation_profile_feature('..') == 'PUNCT'

    def test_should_return_nopunct(self):
        assert get_punctuation_profile_feature('abc') == 'NOPUNCT'
