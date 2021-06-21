import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional

from lxml import etree

from pygrobid.document.layout_document import LayoutDocument, LayoutToken,  LayoutLine
from pygrobid.external.pdfalto.parser import parse_alto_root


@dataclass
class LayoutModelData:
    data_line: str
    layout_line: Optional[LayoutLine] = None
    layout_token: Optional[LayoutToken] = None

    @property
    def label_token_text(self):
        return self.data_line.split(' ')[0]


class ModelDataGenerator(ABC):
    def iter_data_lines_for_xml_root(
        self,
        root: etree.ElementBase
    ) -> Iterable[str]:
        return self.iter_data_lines_for_layout_document(
            parse_alto_root(root)
        )

    @abstractmethod
    def iter_model_data_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> Iterable[LayoutModelData]:
        pass

    def iter_data_lines_for_layout_document(  # pylint: disable=too-many-locals
        self,
        layout_document: LayoutDocument
    ) -> Iterable[str]:
        return (
            model_data.data_line
            for model_data in self.iter_model_data_for_layout_document(layout_document)
        )


def feature_linear_scaling_int(pos: int, total: int, bin_count: int) -> int:
    """
    Given an integer value between 0 and total, discretized into nbBins following a linear scale
    Adapted from:
    grobid-core/src/main/java/org/grobid/core/features/FeatureFactory.java
    """
    if pos >= total:
        return bin_count
    if pos <= 0:
        return 0
    return math.floor((pos / total) * bin_count)


def get_token_font_status(previous_token: Optional[LayoutToken], current_token: LayoutToken):
    if not previous_token:
        return 'NEWFONT'
    return (
        'SAMEFONT' if current_token.font.font_family == previous_token.font.font_family
        else 'NEWFONT'
    )


def get_token_font_size_feature(
    previous_token: Optional[LayoutToken],
    current_token: LayoutToken
):
    if not previous_token:
        return 'HIGHERFONT'
    previous_font_size = previous_token.font.font_size
    current_font_size = current_token.font.font_size
    if not previous_font_size or not current_font_size:
        return 'HIGHERFONT'
    if previous_font_size < current_font_size:
        return 'HIGHERFONT'
    if previous_font_size > current_font_size:
        return 'LOWERFONT'
    return 'SAMEFONTSIZE'


def get_digit_feature(text: str) -> str:
    if text.isdigit():
        return 'ALLDIGIT'
    for c in text:
        if c.isdigit():
            return 'CONTAINSDIGITS'
    return 'NODIGIT'


def get_capitalisation_feature(text: str) -> str:
    if text and all(not c.islower() for c in text):
        return 'ALLCAP'
    if text and text[0].isupper():
        return 'INITCAP'
    return 'NOCAPS'


class PunctuationProfileValues:
    OPENBRACKET = 'OPENBRACKET'
    ENDBRACKET = 'ENDBRACKET'
    DOT = 'DOT'
    COMMA = 'COMMA'
    HYPHEN = 'HYPHEN'
    QUOTE = 'QUOTE'
    PUNCT = 'PUNCT'
    NOPUNCT = 'NOPUNCT'


PUNCTUATION_PROFILE_MAP = {
    '(': PunctuationProfileValues.OPENBRACKET,
    '[': PunctuationProfileValues.OPENBRACKET,
    ')': PunctuationProfileValues.ENDBRACKET,
    ']': PunctuationProfileValues.ENDBRACKET,
    '.': PunctuationProfileValues.DOT,
    ',': PunctuationProfileValues.COMMA,
    '-': PunctuationProfileValues.HYPHEN,
    '–': PunctuationProfileValues.HYPHEN,
    '"': PunctuationProfileValues.QUOTE,
    '\'': PunctuationProfileValues.QUOTE,
    '`': PunctuationProfileValues.QUOTE,
    '’': PunctuationProfileValues.QUOTE
}


IS_PUNCT_PATTERN = r"^[\,\:;\?\.]+$"


def get_line_status(token_index: int, token_count: int) -> str:
    return (
        'LINEEND' if token_index == token_count - 1
        else (
            'LINESTART' if token_index == 0
            else 'LINEIN'
        )
    )


class RelativeFontSizeFeature:
    def __init__(self, layout_tokens: Iterable[LayoutToken]):
        font_sizes = [
            layout_token.font.font_size
            for layout_token in layout_tokens
            if layout_token.font.font_size
        ]
        self.largest_font_size = max(font_sizes) if font_sizes else 0.0
        self.smallest_font_size = min(font_sizes) if font_sizes else 0.0
        self.mean_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0.0

    def is_largest_font_size(self, layout_token: LayoutToken):
        return layout_token.font.font_size == self.largest_font_size

    def is_smallest_font_size(self, layout_token: LayoutToken):
        return layout_token.font.font_size == self.smallest_font_size

    def is_larger_than_average_font_size(self, layout_token: LayoutToken):
        if not layout_token.font.font_size:
            return False
        return layout_token.font.font_size > self.mean_font_size


class LineIndentationStatusFeature:
    def __init__(self):
        self._line_start_x = None
        self._is_new_line = True
        self._is_indented = False

    def on_new_line(self):
        self._is_new_line = True

    def get_is_indented_and_update(self, layout_token: LayoutToken):
        if self._is_new_line and layout_token.coordinates and layout_token.text:
            previous_line_start_x = self._line_start_x
            self._line_start_x = layout_token.coordinates.x
            character_width = layout_token.coordinates.width / len(layout_token.text)
            if previous_line_start_x is not None:
                if self._line_start_x - previous_line_start_x > character_width:
                    self._is_indented = True
                if previous_line_start_x - self._line_start_x > character_width:
                    self._is_indented = False
        self._is_new_line = False
        return self._is_indented


def get_punctuation_profile_feature(text: str) -> str:
    result = PUNCTUATION_PROFILE_MAP.get(text)
    if not result and re.match(IS_PUNCT_PATTERN, text):
        return PunctuationProfileValues.PUNCT
    if not result:
        return PunctuationProfileValues.NOPUNCT
    return result


def get_str_bool_feature_value(value: bool) -> str:
    return '1' if value else '0'


class CommonLayoutTokenFeatures(ABC):
    def __init__(self, layout_token: LayoutToken) -> None:
        self.layout_token = layout_token
        self.token_text = layout_token.text or ''

    def get_str_is_single_char(self) -> str:
        return get_str_bool_feature_value(len(self.token_text) == 1)

    def get_digit_status(self) -> str:
        return get_digit_feature(self.token_text)

    def get_capitalisation_status(self) -> str:
        if self.get_digit_status() == 'ALLDIGIT':
            return 'NOCAPS'
        return get_capitalisation_feature(self.token_text)

    def get_punctuation_profile(self) -> str:
        return get_punctuation_profile_feature(self.token_text)

    def get_dummy_str_is_common_name(self) -> str:
        return '0'

    def get_dummy_str_is_first_name(self) -> str:
        return '0'

    def get_dummy_str_is_last_name(self) -> str:
        return '0'

    def get_dummy_str_is_known_title(self) -> str:
        return '0'

    def get_dummy_str_is_known_suffix(self) -> str:
        return '0'

    def get_dummy_label(self) -> str:
        return '0'
