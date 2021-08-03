import re
from typing import Iterable, List


# delimters mostly copied from:
# https://github.com/kermitt2/delft/blob/v0.2.6/delft/utilities/Tokenizer.py
# added: `@`, `#`
DELIMITERS = "\n\r\t\f\u00A0([ •*,:;?.!/#)-−–‐\"“”‘’'`$]*\u2666\u2665\u2663\u2660\u00A0@"
DELIMITERS_REGEX = r'(' + r'|'.join(map(re.escape, DELIMITERS)) + r'|\s)'


def iter_tokenized_tokens(text: str, keep_whitespace: bool = False) -> Iterable[str]:
    for token in re.split(DELIMITERS_REGEX, text):
        if not keep_whitespace and not token.strip():
            continue
        yield token


def get_tokenized_tokens(text: str, **kwargs) -> List[str]:
    return list(iter_tokenized_tokens(text, **kwargs))
