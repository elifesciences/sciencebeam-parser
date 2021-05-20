from pygrobid.document.layout_document import (
    LayoutToken,
    LayoutLine,
    LayoutBlock,
    LayoutPage,
    LayoutDocument,
    retokenize_layout_document
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
        layout_document = LayoutDocument(
            pages=[LayoutPage(blocks=[LayoutBlock(lines=[LayoutLine(tokens=[
                LayoutToken('token1 token2', whitespace='\n')
            ])])])]
        )
        retokenized_layout_document = retokenize_layout_document(layout_document)
        line = retokenized_layout_document.pages[0].blocks[0].lines[0]
        assert [t.text for t in line.tokens] == ['token1', 'token2']
        assert [t.whitespace for t in line.tokens] == [' ', '\n']
