import logging
import re
from typing import Counter, Iterable, List, Optional, Set

from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutLine,
    LayoutToken
)
from sciencebeam_parser.models.data import (
    ContextAwareLayoutTokenFeatures,
    DocumentFeaturesContext,
    ModelDataGenerator,
    LayoutModelData,
    feature_linear_scaling_int,
    _LINESCALE,
    get_str_bool_feature_value
)


LOGGER = logging.getLogger(__name__)


NBSP = '\u00A0'


def format_feature_text(text: str) -> str:
    return re.sub(" |\t", NBSP, text.strip())


NBBINS_POSITION = 12

EMPTY_LAYOUT_TOKEN = LayoutToken('')
EMPTY_LAYOUT_LINE = LayoutLine([])


def get_block_status(line_index: int, line_count: int) -> str:
    return (
        'BLOCKSTART' if line_index == 0
        else (
            'BLOCKEND'
            if line_index == line_count - 1
            else 'BLOCKIN'
        )
    )


def get_page_status(
    block_index: int, block_count: int,
    is_first_block_token: bool,
    is_last_block_token: bool
) -> str:
    return (
        'PAGESTART' if block_index == 0 and is_first_block_token
        else (
            'PAGEEND'
            if block_index == block_count - 1 and is_last_block_token
            else 'PAGEIN'
        )
    )


# based on:
# https://github.com/kermitt2/grobid/blob/0.6.2/grobid-core/src/main/java/org/grobid/core/features/FeatureFactory.java#L359-L367
def get_text_pattern(text: str) -> str:
    # Note: original code is meant to shadow numbers but are actually removed
    return re.sub(r'[^a-zA-Z ]', '', text).lower()


class SegmentationLineFeatures(ContextAwareLayoutTokenFeatures):
    def __init__(
        self,
        document_features_context: DocumentFeaturesContext,
        layout_token: LayoutToken = EMPTY_LAYOUT_TOKEN
    ):
        super().__init__(
            layout_token,
            document_features_context=document_features_context,
            layout_line=EMPTY_LAYOUT_LINE
        )
        self.line_text = ''
        self.second_token_text = ''
        self.page_blocks: List[LayoutBlock] = []
        self.page_block_index: int = 0
        self.block_lines: List[LayoutLine] = []
        self.block_line_index: int = 0
        self.previous_layout_token: Optional[LayoutToken] = None
        self.max_block_line_text_length = 0
        self.document_token_count = 0
        self.document_token_index = 0
        self.is_repetitive_pattern: bool = False
        self.is_first_repetitive_pattern: bool = False

    def get_block_status(self) -> str:
        return get_block_status(self.block_line_index, len(self.block_lines))

    def get_page_status(self) -> str:
        return get_page_status(
            self.page_block_index, len(self.page_blocks),
            is_first_block_token=self.block_line_index == 0,
            is_last_block_token=self.block_line_index == len(self.block_lines) - 1
        )

    def get_formatted_whole_line_feature(self) -> str:
        return format_feature_text(self.line_text)

    def get_str_is_repetitive_pattern(self) -> str:
        return get_str_bool_feature_value(self.is_repetitive_pattern)

    def get_str_is_first_repetitive_pattern(self) -> str:
        return get_str_bool_feature_value(self.is_first_repetitive_pattern)

    def get_dummy_str_is_repetitive_pattern(self) -> str:
        return '0'

    def get_dummy_str_is_first_repetitive_pattern(self) -> str:
        return '0'

    def get_dummy_str_is_main_area(self) -> str:
        # whether the block's bounding box intersects with the page bounding box
        return '1'

    def get_str_block_relative_line_length_feature(self) -> str:
        return str(feature_linear_scaling_int(
            len(self.line_text),
            self.max_block_line_text_length,
            _LINESCALE
        ))

    def get_str_relative_document_position(self) -> str:
        return str(feature_linear_scaling_int(
            self.document_token_index,
            self.document_token_count,
            NBBINS_POSITION
        ))


class SegmentationLineFeaturesProvider:
    def __init__(
        self,
        document_features_context: DocumentFeaturesContext,
        use_first_token_of_block: bool
    ):
        self.document_features_context = document_features_context
        self.use_first_token_of_block = use_first_token_of_block

    def iter_line_features(  # pylint: disable=too-many-locals
        self,
        layout_document: LayoutDocument
    ) -> Iterable[SegmentationLineFeatures]:
        segmentation_line_features = SegmentationLineFeatures(
            document_features_context=self.document_features_context
        )
        previous_token: Optional[LayoutToken] = None
        segmentation_line_features.document_token_count = sum(
            len(line.tokens)
            for block in layout_document.iter_all_blocks()
            for line in block.lines
        )
        pattern_candididate_block_iterable = (
            block
            for page in layout_document.pages
            for block_index, block in enumerate(page.blocks)
            if block_index < 2 or block_index > len(page.blocks) - 2
        )
        pattern_candididate_line_iterable = (
            block.lines[0]
            for block in pattern_candididate_block_iterable
            if block.lines and block.lines[0].tokens
        )
        all_pattern_by_line_id = {
            id(line): get_text_pattern(line.text)
            for line in pattern_candididate_line_iterable
        }
        LOGGER.debug('all_pattern_by_line_id: %s', all_pattern_by_line_id)
        pattern_by_line_id = {
            key: value
            for key, value in all_pattern_by_line_id.items()
            if len(value) >= 8  # Java GROBID sometimes counts an additional trailing space
        }
        pattern_counter = Counter(pattern_by_line_id.values())
        LOGGER.debug('pattern_counter: %s', pattern_counter)
        seen_repetitive_patterns: Set[str] = set()
        document_token_index = 0
        for page in layout_document.pages:
            blocks = page.blocks
            segmentation_line_features.page_blocks = blocks
            for block_index, block in enumerate(blocks):
                segmentation_line_features.page_block_index = block_index
                block_lines = block.lines
                segmentation_line_features.block_lines = block_lines
                block_line_texts = [line.text for line in block_lines]
                max_block_line_text_length = max(len(text) for text in block_line_texts)
                first_block_token = next(iter(block.iter_all_tokens()), None)
                assert first_block_token
                for line_index, line in enumerate(block_lines):
                    segmentation_line_features.document_token_index = document_token_index
                    document_token_index += len(line.tokens)
                    segmentation_line_features.layout_line = line
                    segmentation_line_features.block_line_index = line_index
                    segmentation_line_features.max_block_line_text_length = (
                        max_block_line_text_length
                    )
                    line_text = block_line_texts[line_index]
                    retokenized_token_texts = re.split(r" |\t|\f|\u00A0", line_text)
                    if not retokenized_token_texts:
                        continue
                    if self.use_first_token_of_block:
                        # Java GROBID uses the first token in the block
                        token = first_block_token
                    else:
                        token = line.tokens[0]
                    segmentation_line_features.layout_token = token
                    segmentation_line_features.line_text = line_text
                    segmentation_line_features.concatenated_line_tokens_text = line_text
                    segmentation_line_features.token_text = retokenized_token_texts[0].strip()
                    segmentation_line_features.second_token_text = (
                        retokenized_token_texts[1] if len(retokenized_token_texts) >= 2 else ''
                    )
                    segmentation_line_features.previous_layout_token = previous_token
                    line_pattern = pattern_by_line_id.get(id(line), '')
                    LOGGER.debug('line_pattern: %r', line_pattern)
                    segmentation_line_features.is_repetitive_pattern = (
                        pattern_counter[line_pattern] > 1
                    )
                    segmentation_line_features.is_first_repetitive_pattern = (
                        segmentation_line_features.is_repetitive_pattern
                        and line_pattern not in seen_repetitive_patterns
                    )
                    if segmentation_line_features.is_first_repetitive_pattern:
                        seen_repetitive_patterns.add(line_pattern)
                    yield segmentation_line_features
                    previous_token = token


class SegmentationDataGenerator(ModelDataGenerator):
    def __init__(
        self,
        document_features_context: DocumentFeaturesContext,
        use_first_token_of_block: bool
    ):
        self.document_features_context = document_features_context
        self.use_first_token_of_block = use_first_token_of_block

    def iter_model_data_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> Iterable[LayoutModelData]:
        features_provider = SegmentationLineFeaturesProvider(
            document_features_context=self.document_features_context,
            use_first_token_of_block=self.use_first_token_of_block
        )
        for features in features_provider.iter_line_features(
            layout_document
        ):
            line_features: List[str] = [
                features.token_text,
                features.second_token_text or features.token_text,
                features.get_lower_token_text(),
                features.get_prefix(1),
                features.get_prefix(2),
                features.get_prefix(3),
                features.get_prefix(4),
                features.get_block_status(),
                features.get_page_status(),
                features.get_token_font_status(),
                features.get_token_font_size_feature(),
                features.get_str_is_bold(),
                features.get_str_is_italic(),
                features.get_capitalisation_status_using_allcap(),
                features.get_digit_status_using_containsdigits(),
                features.get_str_is_single_char(),
                features.get_dummy_str_is_proper_name(),
                features.get_dummy_str_is_common_name(),
                features.get_dummy_str_is_first_name(),
                features.get_dummy_str_is_year(),
                features.get_dummy_str_is_month(),
                features.get_dummy_str_is_email(),
                features.get_dummy_str_is_http(),
                features.get_str_relative_document_position(),
                features.get_dummy_str_relative_page_position(),
                features.get_line_punctuation_profile(),
                features.get_line_punctuation_profile_length_feature(),
                features.get_str_block_relative_line_length_feature(),
                features.get_dummy_str_is_bitmap_around(),
                features.get_dummy_str_is_vector_around(),
                features.get_str_is_repetitive_pattern(),
                features.get_str_is_first_repetitive_pattern(),
                features.get_dummy_str_is_main_area(),
                features.get_formatted_whole_line_feature()
            ]

            if len(line_features) != 34:
                raise AssertionError(
                    'expected features to have 34 features, but was=%d (features=%s)' % (
                        len(line_features), line_features
                    )
                )
            yield LayoutModelData(
                layout_line=features.layout_line,
                data_line=' '.join(line_features)
            )
