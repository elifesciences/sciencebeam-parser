from sciencebeam_parser.document.layout_document import (
    LayoutLineDescriptor,
    LayoutPageCoordinates,
    LayoutToken,
    LayoutLine,
    LayoutBlock,
    LayoutPage,
    LayoutDocument,
    LayoutTokensText,
    get_merged_coordinates_list,
    retokenize_layout_document,
    remove_empty_blocks
)


class TestGetMergedCoordinatesList:
    def test_should_merge_coordinates_on_same_line(self):
        assert get_merged_coordinates_list([
            LayoutPageCoordinates(x=10, y=10, width=100, height=100, page_number=1),
            LayoutPageCoordinates(x=110, y=10, width=100, height=100, page_number=1)
        ]) == [LayoutPageCoordinates(x=10, y=10, width=110 - 10 + 100, height=100, page_number=1)]

    def test_should_merge_coordinates_above_each_other(self):
        assert get_merged_coordinates_list([
            LayoutPageCoordinates(x=10, y=10, width=100, height=100, page_number=1),
            LayoutPageCoordinates(x=10, y=110, width=100, height=100, page_number=1)
        ]) == [LayoutPageCoordinates(x=10, y=10, width=100, height=110 - 10 + 100, page_number=1)]

    def test_should_not_merge_coordinates_on_different_pages(self):
        coordinates_list = [
            LayoutPageCoordinates(x=10, y=10, width=100, height=100, page_number=1),
            LayoutPageCoordinates(x=110, y=10, width=100, height=100, page_number=2)
        ]
        assert get_merged_coordinates_list(coordinates_list) == coordinates_list


class TestLayoutBlock:
    def test_should_parse_text_with_two_tokens(self):
        layout_block = LayoutBlock.for_text('token1 token2', tail_whitespace='\n')
        assert [
            (token.text, token.whitespace)
            for token in layout_block.lines[0].tokens
        ] == [
            ('token1', ' '),
            ('token2', '\n')
        ]

    def test_should_parse_text_with_punctuation_tokens(self):
        layout_block = LayoutBlock.for_text('token1. token2', tail_whitespace='\n')
        assert [
            (token.text, token.whitespace)
            for token in layout_block.lines[0].tokens
        ] == [
            ('token1', ''),
            ('.', ' '),
            ('token2', '\n')
        ]

    def test_should_create_lines_based_on_line_descriptor(self):
        line_descriptor_1 = LayoutLineDescriptor(line_id=1)
        line_descriptor_2 = LayoutLineDescriptor(line_id=2)
        line_tokens_1 = [
            LayoutToken(text, line_descriptor=line_descriptor_1)
            for text in ['token1.1', 'token1.2']
        ]
        line_tokens_2 = [
            LayoutToken(text, line_descriptor=line_descriptor_2)
            for text in ['token2.1', 'token2.2']
        ]
        layout_block = LayoutBlock.for_tokens(line_tokens_1 + line_tokens_2)
        assert len(layout_block.lines) == 2
        assert layout_block.lines[0].tokens == line_tokens_1
        assert layout_block.lines[1].tokens == line_tokens_2


class TestLayoutTokensText:
    def test_should_select_tokens_based_on_index(self):
        token_1 = LayoutToken(text='token1', whitespace=' ')
        token_2 = LayoutToken(text='token2', whitespace=' ')
        layout_tokens_text = LayoutTokensText(LayoutBlock.for_tokens([
            token_1,
            token_2
        ]))
        assert str(layout_tokens_text) == 'token1 token2'
        assert layout_tokens_text.get_layout_tokens_between(
            0, 1
        ) == [token_1]
        assert layout_tokens_text.get_layout_tokens_between(
            len(token_1.text) - 1, len(token_1.text)
        ) == [token_1]
        assert layout_tokens_text.get_layout_tokens_between(
            len(token_1.text), len(token_1.text) + 1
        ) == []
        assert layout_tokens_text.get_layout_tokens_between(
            len(token_1.text) + 1, len(token_1.text) + 2
        ) == [token_2]
        assert layout_tokens_text.get_layout_tokens_between(
            len(token_1.text) + 1 + len(token_2.text) - 1,
            len(token_1.text) + 1 + len(token_2.text)
        ) == [token_2]
        assert layout_tokens_text.get_layout_tokens_between(
            len(token_1.text) + 1 + len(token_2.text),
            len(token_1.text) + 1 + len(token_2.text) + 1
        ) == []


class TestRetokenizeLayoutDocument:
    def test_should_not_retokenize_document_with_valid_tokens(self):
        layout_document = LayoutDocument(
            pages=[LayoutPage(
                blocks=[LayoutBlock.for_tokens([
                    LayoutToken('token1')
                ])],
                graphics=[]
            )]
        )
        retokenized_layout_document = retokenize_layout_document(layout_document)
        line = retokenized_layout_document.pages[0].blocks[0].lines[0]
        assert [t.text for t in line.tokens] == ['token1']

    def test_should_retokenize_document_with_placeholders(self):
        text = 'token1 token2'
        layout_document = LayoutDocument(
            pages=[LayoutPage(
                blocks=[LayoutBlock.for_tokens([
                    LayoutToken(
                        text, whitespace='\n',
                        coordinates=LayoutPageCoordinates(x=10, y=10, width=100, height=50)
                    )
                ])],
                graphics=[]
            )]
        )
        retokenized_layout_document = retokenize_layout_document(layout_document)
        line = retokenized_layout_document.pages[0].blocks[0].lines[0]
        assert [t.text for t in line.tokens] == ['token1', 'token2']
        assert [t.whitespace for t in line.tokens] == [' ', '\n']
        assert line.tokens[0].coordinates.x == 10.0
        assert line.tokens[0].coordinates.width == 100 * len('token1') / len(text)
        assert line.tokens[1].coordinates.x == 10.0 + 100 * len('token1 ') / len(text)
        assert line.tokens[1].coordinates.width == 100 * len('token2') / len(text)

    def test_should_remove_blank_token(self):
        layout_document = LayoutDocument(
            pages=[LayoutPage(
                blocks=[LayoutBlock.for_tokens([
                    LayoutToken(' ')
                ])],
                graphics=[]
            )]
        )
        retokenized_layout_document = retokenize_layout_document(layout_document)
        line = retokenized_layout_document.pages[0].blocks[0].lines[0]
        assert line.tokens == []


class TestRemoveEmptyBlocks:
    def test_should_not_remove_empty_line_block_and_page(self):
        layout_document = LayoutDocument(
            pages=[
                LayoutPage(
                    blocks=[LayoutBlock(lines=[LayoutLine(tokens=[
                        LayoutToken('token1')
                    ])])],
                    graphics=[]
                ),
                LayoutPage(
                    blocks=[LayoutBlock(lines=[LayoutLine(tokens=[
                    ])])],
                    graphics=[]
                ),
            ]
        )
        cleaned_layout_document = remove_empty_blocks(layout_document)
        assert len(cleaned_layout_document.pages) == 1
        line = cleaned_layout_document.pages[0].blocks[0].lines[0]
        assert [t.text for t in line.tokens] == ['token1']
