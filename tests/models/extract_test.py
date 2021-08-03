from sciencebeam_parser.document.layout_document import LayoutBlock
from sciencebeam_parser.models.extract import get_regex_cleaned_layout_block_with_prefix_suffix


class TestGetRegexCleanedLayoutBlockWithPrefixSuffix:
    def test_should_return_original_block_for_non_matching_regex(self):
        layout_block = LayoutBlock.for_text('test')
        prefix_block, cleaned_block, suffix_block = (
            get_regex_cleaned_layout_block_with_prefix_suffix(
                layout_block,
                r'other'
            )
        )
        assert not prefix_block.lines
        assert cleaned_block == layout_block
        assert not suffix_block.lines

    def test_should_return_original_block_for_empty_block(self):
        layout_block = LayoutBlock(lines=[])
        prefix_block, cleaned_block, suffix_block = (
            get_regex_cleaned_layout_block_with_prefix_suffix(
                layout_block,
                r'other'
            )
        )
        assert not prefix_block.lines
        assert cleaned_block == layout_block
        assert not suffix_block.lines

    def test_should_return_prefix_for_prefix_match(self):
        layout_block = LayoutBlock.for_text('a b c d')
        prefix_block, cleaned_block, suffix_block = (
            get_regex_cleaned_layout_block_with_prefix_suffix(
                layout_block,
                r'.*?(b.*)'
            )
        )
        assert prefix_block.text == 'a'
        assert cleaned_block.text == 'b c d'
        assert not suffix_block.lines

    def test_should_return_suffix_for_suffix_match(self):
        layout_block = LayoutBlock.for_text('a b c d')
        prefix_block, cleaned_block, suffix_block = (
            get_regex_cleaned_layout_block_with_prefix_suffix(
                layout_block,
                r'(.*)d'
            )
        )
        assert not prefix_block.lines
        assert cleaned_block.text == 'a b c'
        assert suffix_block.text == 'd'

    def test_should_return_prefix_suffix_for_prefix_suffix_match(self):
        layout_block = LayoutBlock.for_text('a b c d')
        prefix_block, cleaned_block, suffix_block = (
            get_regex_cleaned_layout_block_with_prefix_suffix(
                layout_block,
                r'a(.*)d'
            )
        )
        assert prefix_block.text == 'a'
        assert cleaned_block.text == 'b c'
        assert suffix_block.text == 'd'
