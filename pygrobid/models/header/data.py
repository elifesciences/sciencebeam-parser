from typing import Iterable

from pygrobid.document.layout_document import LayoutDocument
from pygrobid.models.data import ModelDataGenerator


class HeaderDataGenerator(ModelDataGenerator):
    def iter_data_lines_for_layout_document(  # pylint: disable=too-many-locals
        self,
        layout_document: LayoutDocument
    ) -> Iterable[str]:
        for block in layout_document.iter_all_blocks():
            block_lines = block.lines
            for line_index, line in enumerate(block_lines):
                line_tokens = line.tokens
                for token_index, token in enumerate(line_tokens):
                    token_text: str = token.text or ''
                    line_status = (
                        'LINESTART' if token_index == 0
                        else (
                            'LINEEND' if token_index == len(line_tokens) - 1
                            else 'LINEIN'
                        )
                    )
                    block_status = (
                        'BLOCKSTART' if line_index == 0 and line_status == 'LINESTART'
                        else (
                            'BLOCKEND'
                            if line_index == len(block_lines) - 1 and line_status == 'LINEEND'
                            else 'BLOCKIN'
                        )
                    )
                    alignment_status = 'ALIGNEDLEFT'  # may also be 'LINEINDENT'
                    font_status = 'SAMEFONT'  # may also be 'NEWFONT
                    font_size = 'SAMEFONTSIZE'  # one of HIGHERFONT, SAMEFONTSIZE, LOWERFONT
                    is_bold = False
                    is_italic = False
                    digit_status = 'NODIGIT'  # one of ALLDIGIT, CONTAINDIGIT, NODIGIT
                    capitalisation_status = 'NOCAPS'  # one of INITCAP, ALLCAPS, NOCAPS
                    if digit_status == 'ALLDIGIT':
                        capitalisation_status = 'NOCAPS'
                    is_single_char = len(token_text) == 1
                    is_proper_name = False
                    is_common_name = False
                    is_year = False
                    is_month = False
                    is_location_name = False
                    is_email = False
                    is_http = False
                    # one of NOPUNCT, OPENBRACKET, ENDBRACKET, DOT, COMMA, HYPHEN, QUOTE, PUNCT
                    punct_type = 'NOPUNCT'
                    is_largest_font = False
                    is_smallest_font = False
                    is_larger_than_average_font = False
                    label = '0'
                    yield ' '.join([
                        token_text,
                        token_text.lower(),
                        token_text[:1],
                        token_text[:2],
                        token_text[:3],
                        token_text[:4],
                        token_text[-1:],
                        token_text[-2:],
                        token_text[-3:],
                        token_text[-4:],
                        block_status,
                        line_status,
                        alignment_status,
                        font_status,
                        font_size,
                        '1' if is_bold else '0',
                        '1' if is_italic else '0',
                        capitalisation_status,
                        digit_status,
                        '1' if is_single_char else '0',
                        '1' if is_proper_name else '0',
                        '1' if is_common_name else '0',
                        '1' if is_year else '0',
                        '1' if is_month else '0',
                        '1' if is_location_name else '0',
                        '1' if is_email else '0',
                        '1' if is_http else '0',
                        punct_type,
                        '1' if is_largest_font else '0',
                        '1' if is_smallest_font else '0',
                        '1' if is_larger_than_average_font else '0',
                        label
                    ])
