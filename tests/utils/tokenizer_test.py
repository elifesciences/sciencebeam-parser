from pygrobid.utils.tokenizer import iter_tokenized_tokens


class TestIterTokenizedTokens:
    def test_should_split_on_regular_space(self):
        assert (
            list(iter_tokenized_tokens('token1 token2'))
            == ['token1', 'token2']
        )

    def test_should_split_on_thin_space(self):
        assert (
            list(iter_tokenized_tokens('token1\u2009token2'))
            == ['token1', 'token2']
        )

    def test_should_split_on_line_feed(self):
        assert (
            list(iter_tokenized_tokens('token1\ntoken2'))
            == ['token1', 'token2']
        )

    def test_should_preserve_space(self):
        assert (
            list(iter_tokenized_tokens('token1 token2', keep_whitespace=True))
            == ['token1', ' ', 'token2']
        )

    def test_should_preserve_line_feed(self):
        assert (
            list(iter_tokenized_tokens('token1\ntoken2', keep_whitespace=True))
            == ['token1', '\n', 'token2']
        )
