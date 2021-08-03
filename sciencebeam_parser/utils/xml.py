from typing import Union

from lxml import etree


def get_text_content(node: Union[str, etree.ElementBase]) -> str:
    if node is None:
        return ''
    if isinstance(node, str):
        return str(node)
    return ''.join(node.itertext())
