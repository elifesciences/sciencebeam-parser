from lxml.builder import ElementMaker

from pygrobid.external.pdfalto.parser import parse_alto_root, ALTO_NS


ALTO_E = ElementMaker(namespace=ALTO_NS, nsmap={
    None: ALTO_NS
})


FONT_ID_1 = 'font1'
FONTFAMILY_1 = 'fontfamily1'
FONTSIZE_1 = 11.1

FONT_ID_2 = 'font2'
FONTFAMILY_2 = 'fontfamily2'
FONTSIZE_2 = 22.2

BOLD = 'bold'
ITALICS = 'italics'

TOKEN_1 = 'token1'
TOKEN_2 = 'token2'


class TestParseAltoRoot:
    def test_should_parse_simple_document(self):
        layout_document = parse_alto_root(ALTO_E.alto(
            ALTO_E.Styles(
                ALTO_E.TextStyle(
                    ID=FONT_ID_1,
                    FONTFAMILY=FONTFAMILY_1,
                    FONTSIZE=str(FONTSIZE_1)
                ),
                ALTO_E.TextStyle(
                    ID=FONT_ID_2,
                    FONTFAMILY=FONTFAMILY_2,
                    FONTSIZE=str(FONTSIZE_2),
                    FONTSTYLE=f'{BOLD} {ITALICS}'
                )
            ),
            ALTO_E.Layout(
                ALTO_E.Page(
                    ALTO_E.PrintSpace(
                        ALTO_E.TextBlock(
                            ALTO_E.TextLine(
                                ALTO_E.String(
                                    CONTENT=TOKEN_1,
                                    STYLEREFS=FONT_ID_1
                                ),
                                ALTO_E.String(
                                    CONTENT=TOKEN_2,
                                    STYLEREFS=FONT_ID_2
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
        tokens = layout_document.pages[0].blocks[0].lines[0].tokens
        assert len(tokens) == 2
        token = tokens[0]
        assert token.text == TOKEN_1
        assert token.font.font_family == FONTFAMILY_1
        assert token.font.font_size == FONTSIZE_1
        assert token.font.is_bold is False
        assert token.font.is_italics is False
        token = tokens[1]
        assert token.text == TOKEN_2
        assert token.font.font_family == FONTFAMILY_2
        assert token.font.font_size == FONTSIZE_2
        assert token.font.is_bold is True
        assert token.font.is_italics is True
