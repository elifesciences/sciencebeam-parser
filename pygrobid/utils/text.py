import re


DASH_REGEX = '–'
QUOTE_REGEX = '’'

REGEX_REPLACEMENTS = [
    (DASH_REGEX, '-'),
    (QUOTE_REGEX, "'")
]


def normalize_text(text: str) -> str:
    for pattern, replacement in REGEX_REPLACEMENTS:
        text = re.sub(pattern, replacement, text)
    return text
