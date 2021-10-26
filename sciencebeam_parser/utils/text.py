import re
from typing import Sequence

# mostly copied from:
# https://github.com/kermitt2/grobid/blob/0.6.2/grobid-core/src/main/java/org/grobid/core/utilities/TextUtilities.java#L773-L948
# added: '\u2010' .. '\u2015', '`'
REPLACEMENT_CHARACTER_BY_CHARACTER_MAP = {
    '`': "'",
    '\uFB00': 'ff',
    '\uFB01': 'fi',
    '\uFB02': 'fl',
    '\uFB03': 'ffi',
    '\uFB04': 'ffl',
    '\uFB05': 'ft',
    '\uFB06': 'st',
    '\u00E6': 'ae',
    '\u00C6': 'AE',
    '\u0153': 'oe',
    '\u0152': 'OE',
    '\u2010': '-',
    '\u2011': '-',
    '\u2012': '-',
    '\u2013': '-',
    '\u2014': '-',
    '\u2015': '-',
    '\u201C': '"',
    '\u201D': '"',
    '\u201E': '"',
    '\u201F': '"',
    '\u2019': '\'',
    '\u2018': '\'',
    '\u2022': '•',
    '\u2023': '•',
    '\u2043': '•',
    '\u204C': '•',
    '\u204D': '•',
    '\u2219': '•',
    '\u25C9': '•',
    '\u25D8': '•',
    '\u25E6': '•',
    '\u2619': '•',
    '\u2765': '•',
    '\u2767': '•',
    '\u29BE': '•',
    '\u29BF': '•',
    '\u2217': '*'
}


REPLACEMENT_CHARACTER_BY_CHARACTER_TRANSLATION = str.maketrans(
    REPLACEMENT_CHARACTER_BY_CHARACTER_MAP
)


def normalize_text(text: str) -> str:
    return re.sub(
        r'\s{2,}',
        ' ',
        re.sub(
            r'\s*\n\s*',
            '\n',
            text.translate(REPLACEMENT_CHARACTER_BY_CHARACTER_TRANSLATION),
            flags=re.RegexFlag.MULTILINE
        )
    )


def remove_whitespace(text: str) -> str:
    return re.sub(r'\s', '', text)


def parse_comma_separated_value(s: str, sep: str = ',') -> Sequence[str]:
    s = s.strip()
    if not s:
        return []
    return [item.strip() for item in s.split(sep)]
