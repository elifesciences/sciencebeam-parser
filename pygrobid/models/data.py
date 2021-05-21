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
    if text.isupper():
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
    '"': PunctuationProfileValues.QUOTE,
    '\'': PunctuationProfileValues.QUOTE,
    '`': PunctuationProfileValues.QUOTE,
}


IS_PUNCT_PATTERN = r"^[\,\:;\?\.]+$"


def get_punctuation_profile_feature(text: str) -> str:
    result = PUNCTUATION_PROFILE_MAP.get(text)
    if not result and re.match(IS_PUNCT_PATTERN, text):
        return PunctuationProfileValues.PUNCT
    if not result:
        return PunctuationProfileValues.NOPUNCT
    return result