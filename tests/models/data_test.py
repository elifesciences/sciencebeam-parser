from abc import ABC, abstractmethod

from pygrobid.document.layout_document import (
    LayoutPageCoordinates,
    LayoutFont,
    LayoutToken
)
from pygrobid.models.data import (
    RelativeFontSizeFeature,
    LineIndentationStatusFeature,
    get_block_status_with_blockend_for_single_token,
    get_block_status_with_blockstart_for_single_token,
    get_line_status_with_lineend_for_single_token,
    get_line_status_with_linestart_for_single_token,
    get_token_font_size_feature,
    get_digit_feature,
    get_capitalisation_feature,
    get_punctuation_type_feature,
    get_punctuation_profile_feature,
    get_punctuation_profile_length_for_punctuation_profile_feature,
    get_word_shape_feature
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
    def test_should_detect_indented_blocks(self):
        line_indentation_status_feature = LineIndentationStatusFeature()
        line_indentation_status_feature.on_new_line()
        assert line_indentation_status_feature.get_is_indented_and_update(
            LayoutToken('x', coordinates=LayoutPageCoordinates(x=10, y=10, width=10, height=10))
        ) is False
        line_indentation_status_feature.on_new_line()
        assert line_indentation_status_feature.get_is_indented_and_update(
            LayoutToken('x', coordinates=LayoutPageCoordinates(x=50, y=10, width=10, height=10))
        ) is True


class _TestBaseGetLineStatus(ABC):
    @abstractmethod
    def get_line_status(self, *args) -> str:
        pass

    def test_should_return_linestart_for_first_token(self):
        assert self.get_line_status(0, 10) == 'LINESTART'

    def test_should_return_lineend_for_last_token(self):
        assert self.get_line_status(9, 10) == 'LINEEND'

    def test_should_return_linein_for_token_not_first_or_last(self):
        assert self.get_line_status(1, 10) == 'LINEIN'
        assert self.get_line_status(8, 10) == 'LINEIN'


class TestGetLineStatusWithLineEndForSingleToken(_TestBaseGetLineStatus):
    def get_line_status(self, *args) -> str:
        return get_line_status_with_lineend_for_single_token(*args)

    def test_should_return_lineend_for_single_token(self):
        assert self.get_line_status(0, 1) == 'LINEEND'


class TestGetLineStatusWithLineStartForSingleToken(_TestBaseGetLineStatus):
    def get_line_status(self, *args) -> str:
        return get_line_status_with_linestart_for_single_token(*args)

    def test_should_return_lineend_for_single_token(self):
        assert self.get_line_status(0, 1) == 'LINESTART'


class _TestBaseGetBlockStatus(ABC):
    @abstractmethod
    def get_block_status(self, *args) -> str:
        pass

    def test_should_return_blockstart_for_first_token_on_first_line(self):
        assert self.get_block_status(0, 10, 'LINESTART') == 'BLOCKSTART'

    def test_should_return_blockend_for_last_token_on_last_line(self):
        assert self.get_block_status(9, 10, 'LINEEND') == 'BLOCKEND'

    def test_should_return_blockin_for_line_not_first_or_last(self):
        assert self.get_block_status(1, 10, 'LINESTART') == 'BLOCKIN'
        assert self.get_block_status(8, 10, 'LINEEND') == 'BLOCKIN'

    def test_should_return_blockin_for_first_line_but_not_first_token(self):
        assert self.get_block_status(0, 10, 'LINEIN') == 'BLOCKIN'

    def test_should_return_blockin_for_last_line_but_not_last_token(self):
        assert self.get_block_status(9, 10, 'LINEIN') == 'BLOCKIN'


class TestGetBlockStatusWithBlockEndForSingleToken(_TestBaseGetBlockStatus):
    def get_block_status(self, *args) -> str:
        return get_block_status_with_blockend_for_single_token(*args)

    def test_should_return_blockend_for_single_token(self):
        assert self.get_block_status(0, 1, 'LINEEND') == 'BLOCKEND'


class TestGetBlockStatusWithBlockStartForSingleToken(_TestBaseGetBlockStatus):
    def get_block_status(self, *args) -> str:
        return get_block_status_with_blockstart_for_single_token(*args)

    def test_should_return_blockend_for_single_token(self):
        assert self.get_block_status(0, 1, 'LINESTART') == 'BLOCKSTART'


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


class TestGetPunctuationTypeFeature:
    def test_should_return_openbracket(self):
        assert get_punctuation_type_feature('(') == 'OPENBRACKET'
        assert get_punctuation_type_feature('[') == 'OPENBRACKET'

    def test_should_return_endbracket(self):
        assert get_punctuation_type_feature(')') == 'ENDBRACKET'
        assert get_punctuation_type_feature(']') == 'ENDBRACKET'

    def test_should_return_dot(self):
        assert get_punctuation_type_feature('.') == 'DOT'

    def test_should_return_comma(self):
        assert get_punctuation_type_feature(',') == 'COMMA'

    def test_should_return_hyphen(self):
        assert get_punctuation_type_feature('-') == 'HYPHEN'
        assert get_punctuation_type_feature('–') == 'HYPHEN'

    def test_should_return_quote(self):
        assert get_punctuation_type_feature('"') == 'QUOTE'
        assert get_punctuation_type_feature('\'') == 'QUOTE'
        assert get_punctuation_type_feature('`') == 'QUOTE'
        assert get_punctuation_type_feature('’') == 'QUOTE'

    def test_should_return_punct(self):
        assert get_punctuation_type_feature(',,') == 'PUNCT'
        assert get_punctuation_type_feature('::') == 'PUNCT'
        assert get_punctuation_type_feature(';;') == 'PUNCT'
        assert get_punctuation_type_feature('??') == 'PUNCT'
        assert get_punctuation_type_feature('..') == 'PUNCT'

    def test_should_return_nopunct(self):
        assert get_punctuation_type_feature('abc') == 'NOPUNCT'


class TestGetPunctuationProfileFeature:
    def test_should_return_empty_string_for_empty_string(self):
        assert get_punctuation_profile_feature('') == ''

    def test_should_return_empty_string_for_letters_or_digits(self):
        assert get_punctuation_profile_feature('abc123') == ''

    def test_should_return_empty_string_for_space(self):
        assert get_punctuation_profile_feature(' ') == ''

    def test_should_return_punctuation_characters(self):
        assert get_punctuation_profile_feature('x.,;x') == '.,;'


class TestGetPunctuationProfileLengthForPunctuationPofileFeature:
    def test_should_return_no_for_empty_punctuation_profile(self):
        assert get_punctuation_profile_length_for_punctuation_profile_feature(
            ''
        ) == 'no'

    def test_should_return_length_of_punctuation_profile(self):
        assert get_punctuation_profile_length_for_punctuation_profile_feature(
            '.'
        ) == '1'

    def test_should_return_ten_for_larger_lengths(self):
        assert get_punctuation_profile_length_for_punctuation_profile_feature(
            '.' * 11
        ) == '10'


class TestGetWordShapeFeature:
    def test_should_return_blank_if_input_is_blank(self):
        # Note: this shouldn't really happen as we don't use whitespace tokens
        assert get_word_shape_feature(' ') == ' '

    def test_should_return_capitalisation(self):
        # copied test cases from:
        # https://github.com/kermitt2/grobid/blob/0.6.2/grobid-core/src/test/java/org/grobid/core/utilities/TextUtilitiesTest.java#L210-L228
        assert get_word_shape_feature('This') == 'Xxxx'
        assert get_word_shape_feature('Equals') == 'Xxxx'
        assert get_word_shape_feature("O'Conor") == "X'Xxxx"
        assert get_word_shape_feature('McDonalds') == 'XxXxxx'
        assert get_word_shape_feature('any-where') == 'xx-xxx'
        assert get_word_shape_feature('1.First') == 'd.Xxxx'
        assert get_word_shape_feature('ThisIsCamelCase') == 'XxXxXxXxxx'
        assert get_word_shape_feature('This:happens') == 'Xx:xxx'
        assert get_word_shape_feature('ABC') == 'XXX'
        assert get_word_shape_feature('AC') == 'XX'
        assert get_word_shape_feature('A') == 'X'
        assert get_word_shape_feature('AbA') == 'XxX'
        assert get_word_shape_feature('uü') == 'xx'
        assert get_word_shape_feature('Üwe') == 'Xxx'
        assert get_word_shape_feature('Tes9t99') == 'Xxdxdd'
        assert get_word_shape_feature('T') == 'X'
