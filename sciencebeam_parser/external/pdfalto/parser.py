from typing import Dict, List

from lxml import etree

from sciencebeam_parser.document.layout_document import (
    LayoutPageCoordinates,
    LayoutFont,
    LayoutToken,
    LayoutLine,
    LayoutBlock,
    LayoutPage,
    LayoutDocument,
    EMPTY_FONT
)


ALTO_NS = 'http://www.loc.gov/standards/alto/ns-v3#'
ALTO_NS_MAP = {
    'alto': ALTO_NS
}


def alto_xpath(parent: etree.ElementBase, xpath: str) -> List[etree.ElementBase]:
    return parent.xpath(xpath, namespaces=ALTO_NS_MAP)


class AltoParser:
    def __init__(self):
        self.font_by_id_map: Dict[str, LayoutFont] = {}

    def parse_token(
        self,
        token_node: etree.ElementBase,
        page_index: int
    ) -> LayoutToken:
        return LayoutToken(
            text=token_node.attrib.get('CONTENT') or '',
            font=self.font_by_id_map.get(
                token_node.attrib.get('STYLEREFS'),
                EMPTY_FONT
            ),
            coordinates=LayoutPageCoordinates(
                x=float(token_node.attrib.get('HPOS', 0)),
                y=float(token_node.attrib.get('VPOS', 0)),
                width=float(token_node.attrib.get('WIDTH', 0)),
                height=float(token_node.attrib.get('HEIGHT', 0)),
                page_number=(1 + page_index)
            )
        )

    def parse_line(
        self,
        line_node: etree.ElementBase,
        page_index: int
    ) -> LayoutLine:
        return LayoutLine(tokens=[
            self.parse_token(token_node, page_index=page_index)
            for token_node in alto_xpath(line_node, './/alto:String')
        ])

    def parse_block(
        self,
        block_node: etree.ElementBase,
        page_index: int
    ) -> LayoutBlock:
        return LayoutBlock(lines=[
            self.parse_line(line_node, page_index=page_index)
            for line_node in alto_xpath(block_node, './/alto:TextLine[alto:String]')
        ])

    def parse_page(
        self,
        page_node: etree.ElementBase,
        page_index: int
    ) -> LayoutPage:
        return LayoutPage(blocks=[
            self.parse_block(block_node, page_index=page_index)
            for block_node in alto_xpath(page_node, './/alto:TextBlock')
        ])

    def parse_font(self, font_node: etree.ElementBase) -> LayoutFont:
        font_styles = (font_node.attrib.get('FONTSTYLE') or '').split(' ')
        return LayoutFont(
            font_id=font_node.attrib.get('ID'),
            font_family=font_node.attrib.get('FONTFAMILY'),
            font_size=float(font_node.attrib.get('FONTSIZE')),
            is_bold='bold' in font_styles,
            is_italics='italics' in font_styles,
            is_subscript='subscript' in font_styles,
            is_superscript='superscript' in font_styles
        )

    def parse_font_by_id_map(self, root: etree.ElementBase) -> Dict[str, LayoutFont]:
        fonts = [
            self.parse_font(font_node)
            for font_node in alto_xpath(root, './alto:Styles/alto:TextStyle')
        ]
        return {
            font.font_id: font
            for font in fonts
        }

    def parse_root(self, root: etree.ElementBase) -> LayoutDocument:
        self.font_by_id_map = self.parse_font_by_id_map(root)
        return LayoutDocument(pages=[
            self.parse_page(page_node, page_index=page_index)
            for page_index, page_node in enumerate(alto_xpath(root, './/alto:Page'))
        ])


def parse_alto_root(root: etree.ElementBase) -> LayoutDocument:
    return AltoParser().parse_root(root)
