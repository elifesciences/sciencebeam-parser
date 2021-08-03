from typing import Iterable

from sciencebeam_parser.models.data import (
    ContextAwareLayoutTokenFeatures,
    ContextAwareLayoutTokenModelDataGenerator,
    LayoutModelData
)


class FullTextDataGenerator(ContextAwareLayoutTokenModelDataGenerator):
    def iter_model_data_for_context_layout_token_features(
        self,
        token_features: ContextAwareLayoutTokenFeatures
    ) -> Iterable[LayoutModelData]:
        yield token_features.get_layout_model_data([
            token_features.token_text,
            token_features.get_lower_token_text(),
            token_features.get_prefix(1),
            token_features.get_prefix(2),
            token_features.get_prefix(3),
            token_features.get_prefix(4),
            token_features.get_suffix(1),
            token_features.get_suffix(2),
            token_features.get_suffix(3),
            token_features.get_suffix(4),
            token_features.get_block_status_with_blockstart_for_single_token(),
            token_features.get_line_status_with_linestart_for_single_token(),
            token_features.get_alignment_status(),
            token_features.get_token_font_status(),
            token_features.get_token_font_size_feature(),
            token_features.get_str_is_bold(),
            token_features.get_str_is_italic(),
            token_features.get_capitalisation_status_using_allcap(),
            token_features.get_digit_status_using_containsdigits(),
            token_features.get_str_is_single_char(),
            token_features.get_punctuation_type_feature(),
            token_features.get_dummy_str_relative_document_position(),
            token_features.get_dummy_str_relative_page_position(),
            token_features.get_dummy_str_is_bitmap_around(),
            token_features.get_dummy_callout_type(),
            token_features.get_dummy_str_is_callout_known(),
            token_features.get_str_is_superscript()
        ])
