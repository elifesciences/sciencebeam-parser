from typing import Iterable, List

from pygrobid.models.data import (
    ContextAwareLayoutTokenFeatures,
    ContextAwareLayoutTokenModelDataGenerator,
    LayoutModelData
)


class HeaderDataGenerator(ContextAwareLayoutTokenModelDataGenerator):
    def iter_model_data_for_context_layout_token_features(
        self,
        token_features: ContextAwareLayoutTokenFeatures
    ) -> Iterable[LayoutModelData]:
        token_text: str = token_features.token_text
        features: List[str] = [
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
            token_features.get_block_status(),
            token_features.get_line_status(),
            token_features.get_alignment_status(),
            token_features.get_token_font_status(),
            token_features.get_token_font_size_feature(),
            token_features.get_str_is_bold(),
            token_features.get_str_is_italic(),
            token_features.get_capitalisation_status(),
            token_features.get_digit_status(),
            token_features.get_str_is_single_char(),
            token_features.get_dummy_str_is_proper_name(),
            token_features.get_dummy_str_is_common_name(),
            token_features.get_dummy_str_is_year(),
            token_features.get_dummy_str_is_month(),
            token_features.get_dummy_str_is_location_name(),
            token_features.get_dummy_str_is_email(),
            token_features.get_dummy_str_is_http(),
            token_features.get_punctuation_type_feature(),
            token_features.get_str_is_largest_font_size(),
            token_features.get_str_is_smallest_font_size(),
            token_features.get_str_is_larger_than_average_font_size(),
            token_features.get_dummy_label()
        ]
        yield LayoutModelData(
            layout_line=token_features.layout_line,
            layout_token=token_features.layout_token,
            data_line=' '.join(features)
        )
