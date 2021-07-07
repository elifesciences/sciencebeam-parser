from pygrobid.processors.ref_matching import (
    get_normalized_key_text,
    get_token_prefix_normalized_key_text,
    SimpleContentIdMatcher
)


CONTENT_ID_1 = 'id1'
CONTENT_ID_2 = 'id2'

OTHER_TEXT_1 = 'Other 1'


class TestGetNormalizedKeyText:
    def test_should_convert_to_lower_case(self):
        assert get_normalized_key_text('TeXt') == 'text'

    def test_should_remove_punctuation(self):
        assert get_normalized_key_text('text.,;:') == 'text'

    def test_should_remove_whitespace_characters(self):
        assert get_normalized_key_text('text\n\r\t ') == 'text'

    def test_should_not_remove_digits(self):
        assert get_normalized_key_text('text 123') == 'text123'


class TestGetTokenPrefixNormalizedKeyText:
    def test_should_only_include_initial_letters_of_each_token(self):
        assert get_token_prefix_normalized_key_text('figure 1') == 'f1'

    def test_should_not_remove_digits(self):
        assert get_token_prefix_normalized_key_text('figure 123') == 'f123'

    def test_should_not_shorted_tokens_containing_digits(self):
        assert get_token_prefix_normalized_key_text('figure x123a') == 'fx123a'


class TestSimpleContentIdMatcher:
    def test_should_match_on_exact_match(self):
        matcher = SimpleContentIdMatcher({
            CONTENT_ID_1: 'Text 1',
            CONTENT_ID_2: OTHER_TEXT_1
        })
        assert matcher.get_id_by_text('Text 1') == CONTENT_ID_1

    def test_should_match_case_insensitive(self):
        matcher = SimpleContentIdMatcher({
            CONTENT_ID_1: 'TeXt 1',
            CONTENT_ID_2: OTHER_TEXT_1
        })
        assert matcher.get_id_by_text('tExt 1') == CONTENT_ID_1

    def test_should_ignore_punctuation(self):
        matcher = SimpleContentIdMatcher({
            CONTENT_ID_1: 'Text 1.',
            CONTENT_ID_2: OTHER_TEXT_1
        })
        assert matcher.get_id_by_text('Text 1:') == CONTENT_ID_1

    def test_should_ignore_whitespace(self):
        matcher = SimpleContentIdMatcher({
            CONTENT_ID_1: ' Text\n1 ',
            CONTENT_ID_2: OTHER_TEXT_1
        })
        assert matcher.get_id_by_text('\nText 1\n') == CONTENT_ID_1

    def test_should_match_on_prefix_and_number(self):
        matcher = SimpleContentIdMatcher({
            CONTENT_ID_1: 'Figure 1',
            CONTENT_ID_2: OTHER_TEXT_1
        })
        assert matcher.get_id_by_text('Fig 1') == CONTENT_ID_1
