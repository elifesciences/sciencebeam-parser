import logging
import re
from itertools import zip_longest
from typing import Mapping, NamedTuple, Optional, Sequence, Tuple, Union

from lxml import etree
from lxml.builder import ElementMaker


LOGGER = logging.getLogger(__name__)


class TagExpression(NamedTuple):
    tag: str
    attrib: Mapping[str, str]

    def create_node(self, *args, element_maker: ElementMaker):
        try:
            return element_maker(self.tag, self.attrib, *args)
        except ValueError as exc:
            raise ValueError(
                'failed to create node with tag=%r, attrib=%r due to %s' % (
                    self.tag, self.attrib, exc
                )
            ) from exc


def parse_tag_expression(tag_expression: str) -> TagExpression:
    match = re.match(r'^([^\[]+)(\[@?([^=]+)="(.+)"\])?$', tag_expression)
    if not match:
        raise ValueError('invalid tag expression: %s' % tag_expression)
    LOGGER.debug('match: %s', match.groups())
    tag_name = match.group(1)
    if match.group(2):
        attrib = {match.group(3): match.group(4)}
    else:
        attrib = {}
    return TagExpression(tag=tag_name, attrib=attrib)


def _get_last_child_or_none(element: etree.ElementBase) -> Optional[etree.ElementBase]:
    try:
        return element[-1]
    except IndexError:
        return None


def _append_text(element: etree.ElementBase, text: Optional[str]) -> None:
    if not text:
        return
    last_child = _get_last_child_or_none(element)
    if last_child is not None and last_child.tail:
        last_child.tail = last_child.tail + '' + text
    elif last_child is not None:
        last_child.tail = text
    elif element.text:
        element.text = element.text + '' + text
    else:
        element.text = text


def _get_common_path(path1: Sequence[str], path2: Sequence[str]) -> Sequence[str]:
    if path1 == path2:
        return path1
    common_path = []
    for path1_element, path2_element in zip_longest(path1, path2):
        if path1_element != path2_element:
            break
        common_path.append(path1_element)
    return common_path


def _get_element_at_path(
    current_element: etree.ElementBase,
    current_path: Sequence[str],
    required_path: Sequence[str],
    element_maker: ElementMaker
) -> Tuple[etree.ElementBase, Sequence[str]]:
    if required_path != current_path:
        common_path = _get_common_path(current_path, required_path)
        LOGGER.debug(
            'required element path: %s -> %s (common path: %s)',
            current_path, required_path, common_path
        )
        for _ in range(len(current_path) - len(common_path)):
            current_element = current_element.getparent()
        current_path = list(common_path)
        for path_fragment in required_path[len(common_path):]:
            try:
                parsed_path_fragment = parse_tag_expression(path_fragment)
                child = parsed_path_fragment.create_node(
                    element_maker=element_maker
                )
            except ValueError as exc:
                raise ValueError('failed to create node for %r due to %s' % (
                    path_fragment, exc
                )) from exc
            current_element.append(child)
            current_element = child
            current_path.append(path_fragment)
    return current_element, current_path


class XmlTreeWriter:
    def __init__(
        self,
        parent: etree.ElementBase,
        element_maker: ElementMaker
    ):
        self.current_element = parent
        self.current_path: Sequence[str] = []
        self.element_maker = element_maker

    @property
    def root(self) -> etree.ElementBase:
        return self.current_element.getroottree().getroot()

    def append_text(self, text: str):
        _append_text(self.current_element, text)

    def append(self, element_or_text: Union[etree.ElementBase, str]):
        if isinstance(element_or_text, str):
            self.append_text(element_or_text)
        else:
            self.current_element.append(element_or_text)

    def append_all(self, *element_or_text_list: Sequence[Union[etree.ElementBase, str]]):
        for element_or_text in element_or_text_list:
            self.append(element_or_text)

    def require_path(self, required_path: Sequence[str]):
        self.current_element, self.current_path = _get_element_at_path(
            self.current_element, self.current_path,
            required_path,
            element_maker=self.element_maker
        )

    def require_path_or_below(self, required_path: Sequence[str]):
        self.require_path(
            _get_common_path(self.current_path, required_path)
        )
