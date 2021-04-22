import logging
import re
from typing import Iterable, List, Optional

from pygrobid.document.layout_document import LayoutDocument
from pygrobid.models.data import ModelDataGenerator, LayoutModelData


LOGGER = logging.getLogger(__name__)


NBSP = '\u00A0'


def format_feature_text(text: str) -> str:
    return re.sub(" |\t", NBSP, text.strip())


class SegmentationDataGenerator(ModelDataGenerator):
    def iter_model_data_for_layout_document(  # pylint: disable=too-many-locals
        self,
        layout_document: LayoutDocument
    ) -> Iterable[LayoutModelData]:
        for page in layout_document.pages:
            blocks = page.blocks
            for block_index, block in enumerate(blocks):
                block_lines = block.lines
                for line_index, line in enumerate(block_lines):
                    line_tokens = line.tokens
                    token_texts: List[str] = [
                        layout_token.text or ''
                        for layout_token in line_tokens
                    ]
                    line_text = ' '.join(token_texts)
                    retokenized_token_texts = re.split(r" |\t|\f|\u00A0", line_text)
                    if not retokenized_token_texts:
                        continue
                    token_text = retokenized_token_texts[0].strip()
                    second_token_text = (
                        retokenized_token_texts[1] if len(retokenized_token_texts) >= 2 else ''
                    )
                    block_status = (
                        'BLOCKSTART' if line_index == 0
                        else (
                            'BLOCKEND'
                            if line_index == len(block_lines) - 1
                            else 'BLOCKIN'
                        )
                    )
                    page_status = (
                        'PAGESTART' if block_index == 0
                        else (
                            'PAGEEND'
                            if block_index == len(blocks) - 1
                            else 'PAGEIN'
                        )
                    )
                    relative_document_position = 0  # position within whole document
                    relative_page_position_char = 0
                    line_length = 0
                    punctuation_profile: Optional[str] = None
                    font_status = 'SAMEFONT'  # may also be 'NEWFONT
                    font_size = 'SAMEFONTSIZE'  # one of HIGHERFONT, SAMEFONTSIZE, LOWERFONT
                    is_bold = False
                    is_italic = False
                    digit_status = 'NODIGIT'  # one of ALLDIGIT, CONTAINDIGIT, NODIGIT
                    capitalisation_status = 'NOCAPS'  # one of INITCAP, ALLCAPS, NOCAPS
                    if digit_status == 'ALLDIGIT':
                        capitalisation_status = 'NOCAPS'
                    is_single_char = len(token_text) == 1
                    is_first_name = False
                    relative_document_position = 0
                    is_proper_name = False
                    is_common_name = False
                    is_year = False
                    is_month = False
                    is_bitmap_around = False
                    is_vector_around = False
                    is_repetitive_pattern = False
                    is_first_repetitive_pattern = False
                    is_main_area = False
                    is_email = False
                    is_http = False
                    # one of NOPUNCT, OPENBRACKET, ENDBRACKET, DOT, COMMA, HYPHEN, QUOTE, PUNCT
                    # punct_type = None
                    formatted_whole_line = format_feature_text(line_text)
                    line_features: List[str] = [
                        token_text,
                        second_token_text or token_text,
                        token_text.lower(),
                        token_text[:1],
                        token_text[:2],
                        token_text[:3],
                        token_text[:4],
                        block_status,
                        # line_status,
                        page_status,
                        font_status,
                        font_size,
                        '1' if is_bold else '0',
                        '1' if is_italic else '0',
                        capitalisation_status,
                        digit_status,
                        '1' if is_single_char else '0',
                        '1' if is_proper_name else '0',
                        '1' if is_common_name else '0',
                        '1' if is_first_name else '0',
                        '1' if is_year else '0',
                        '1' if is_month else '0',
                        '1' if is_email else '0',
                        '1' if is_http else '0',
                        # punct_type,
                        str(relative_document_position),
                        str(relative_page_position_char),
                        punctuation_profile if punctuation_profile else 'no',
                        str(len(punctuation_profile)) if punctuation_profile else '0',
                        str(line_length),
                        '1' if is_bitmap_around else '0',
                        '1' if is_vector_around else '0',
                        '1' if is_repetitive_pattern else '0',
                        '1' if is_first_repetitive_pattern else '0',
                        '1' if is_main_area else '0',
                        formatted_whole_line
                    ]

                    if len(line_features) != 34:
                        raise AssertionError(
                            'expected features to have 34 features, but was=%d (features=%s)' % (
                                len(line_features), line_features
                            )
                        )
                    yield LayoutModelData(
                        layout_line=line,
                        data_line=' '.join(line_features)
                    )
