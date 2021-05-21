from pygrobid.document.layout_document import (
    LayoutCoordinates,
    LayoutToken,
    LayoutLine,
    LayoutBlock,
    LayoutPage,
    LayoutDocument,
    retokenize_layout_document,
    remove_empty_blocks
)


class TestRetokenizeLayoutDocument:
    def test_should_not_retokenize_document_with_valid_tokens(self):
        layout_document = LayoutDocument(
            pages=[LayoutPage(blocks=[LayoutBlock(lines=[LayoutLine(tokens=[
                LayoutToken('token1')
            ])])])]
        )
        retokenized_layout_document = retokenize_layout_document(layout_document)
        line = retokenized_layout_document.pages[0].blocks[0].lines[0]
        assert [t.text for t in line.tokens] == ['token1']

    def test_should_retokenize_document_with_placeholders(self):
        text = 'token1 token2'
        layout_document = LayoutDocument(
            pages=[LayoutPage(blocks=[LayoutBlock(lines=[LayoutLine(tokens=[
                LayoutToken(
                    text, whitespace='\n',
                    coordinates=LayoutCoordinates(x=10, y=10, width=100, height=50)
                )
            ])])])]
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
            pages=[LayoutPage(blocks=[LayoutBlock(lines=[LayoutLine(tokens=[
                LayoutToken(' ')
            ])])])]
        )
        retokenized_layout_document = retokenize_layout_document(layout_document)
        line = retokenized_layout_document.pages[0].blocks[0].lines[0]
        assert line.tokens == []


class TestRemoveEmptyBlocks:
    def test_should_not_remove_empty_line_block_and_page(self):
        layout_document = LayoutDocument(
            pages=[
                LayoutPage(blocks=[LayoutBlock(lines=[LayoutLine(tokens=[
                    LayoutToken('token1')
                ])])]),
                LayoutPage(blocks=[LayoutBlock(lines=[LayoutLine(tokens=[
                ])])]),
            ]
        )
        cleaned_layout_document = remove_empty_blocks(layout_document)
        assert len(cleaned_layout_document.pages) == 1
        line = cleaned_layout_document.pages[0].blocks[0].lines[0]
        assert [t.text for t in line.tokens] == ['token1']
