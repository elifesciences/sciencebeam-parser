from typing import Iterable

from pygrobid.document.layout_document import LayoutDocument
from pygrobid.models.data import (
    ModelDataGenerator,
    LayoutModelData,
    get_line_status,
    CommonLayoutTokenFeatures
)


class NameDataGenerator(ModelDataGenerator):
    def iter_model_data_for_layout_document(  # pylint: disable=too-many-locals
        self,
        layout_document: LayoutDocument
    ) -> Iterable[LayoutModelData]:
        for block in layout_document.iter_all_blocks():
            block_lines = block.lines
            for line in block_lines:
                line_tokens = line.tokens
                token_count = len(line_tokens)
                for token_index, token in enumerate(line_tokens):
                    common_features = CommonLayoutTokenFeatures(token)
                    token_text: str = common_features.token_text
                    line_status = get_line_status(
                        token_index=token_index,
                        token_count=token_count
                    )
                    features = [
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
                        line_status,
                        common_features.get_capitalisation_status(),
                        common_features.get_digit_status(),
                        common_features.get_str_is_single_char(),
                        common_features.get_dummy_str_is_common_name(),
                        common_features.get_dummy_str_is_first_name(),
                        common_features.get_dummy_str_is_last_name(),
                        common_features.get_dummy_str_is_known_title(),
                        common_features.get_dummy_str_is_known_suffix(),
                        common_features.get_punctuation_type_feature(),
                        common_features.get_dummy_label()
                    ]
                    yield LayoutModelData(
                        layout_line=line,
                        layout_token=token,
                        data_line=' '.join(features)
                    )
