from typing import List, Sequence, Union

from lxml import etree


def get_text_content(node: Union[str, etree.ElementBase]) -> str:
    if node is None:
        return ''
    if isinstance(node, str):
        return str(node)
    return ''.join(node.itertext())


def get_text_content_list(nodes: Sequence[Union[str, etree.ElementBase]]) -> List[str]:
    return [
        get_text_content(node)
        for node in nodes
    ]
