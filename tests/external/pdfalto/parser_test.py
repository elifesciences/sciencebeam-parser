from lxml.builder import ElementMaker

from pygrobid.external.pdfalto.parser import parse_alto_root, ALTO_NS


ALTO_E = ElementMaker(namespace=ALTO_NS, nsmap={
    None: ALTO_NS
})


TOKEN_1 = 'token1'


class TestParseAltoRoot:
    def test_should_parse_simple_document(self):
        layout_document = parse_alto_root(ALTO_E.alto(
            ALTO_E.Layout(
                ALTO_E.Page(
                    ALTO_E.PrintSpace(
                        ALTO_E.TextBlock(
                            ALTO_E.TextLine(
                                ALTO_E.String(
                                    CONTENT=TOKEN_1
                                )
                            )
                        )
                    )
                )
            )
        ))
        assert len(layout_document.pages) == 1
        assert len(layout_document.pages[0].blocks) == 1
        assert len(layout_document.pages[0].blocks[0].lines) == 1
        assert len(layout_document.pages[0].blocks[0].lines[0].tokens) == 1
        token = layout_document.pages[0].blocks[0].lines[0].tokens[0]
        assert token.text == TOKEN_1
