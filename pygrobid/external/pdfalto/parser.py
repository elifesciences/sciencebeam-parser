from typing import List

from lxml import etree

from pygrobid.document.layout_document import (
    LayoutToken,
    LayoutLine,
    LayoutBlock,
    LayoutPage,
    LayoutDocument
)


ALTO_NS = 'http://www.loc.gov/standards/alto/ns-v3#'
ALTO_NS_MAP = {
    'alto': ALTO_NS
}


def alto_xpath(parent: etree.ElementBase, xpath: str) -> List[etree.ElementBase]:
    return parent.xpath(xpath, namespaces=ALTO_NS_MAP)


def parse_alto_token(token_node: etree.ElementBase) -> LayoutToken:
    return LayoutToken(
        text=token_node.attrib.get('CONTENT') or ''
    )


def parse_alto_line(line_node: etree.ElementBase) -> LayoutLine:
    return LayoutLine(tokens=[
        parse_alto_token(token_node)
        for token_node in alto_xpath(line_node, './/alto:String')
    ])


def parse_alto_block(block_node: etree.ElementBase) -> LayoutBlock:
    return LayoutBlock(lines=[
        parse_alto_line(line_node)
        for line_node in alto_xpath(block_node, './/alto:TextLine[alto:String]')
    ])


def parse_alto_page(page_node: etree.ElementBase) -> LayoutPage:
    return LayoutPage(blocks=[
        parse_alto_block(block_node)
        for block_node in alto_xpath(page_node, './/alto:TextBlock')
    ])


def parse_alto_root(root: etree.ElementBase) -> LayoutDocument:
    return LayoutDocument(pages=[
        parse_alto_page(page_node)
        for page_node in alto_xpath(root, './/alto:Page')
    ])
