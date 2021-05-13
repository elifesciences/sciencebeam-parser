import logging
from typing import Union

from lxml import etree
from lxml.etree import Element, ElementTree


LOGGER = logging.getLogger(__name__)


T_XSLT_Input = Union[Element, ElementTree]


def _to_xslt_input(value: Union[bytes, str, T_XSLT_Input]) -> T_XSLT_Input:
    if isinstance(value, (bytes, str)):
        parser = etree.XMLParser(recover=True)
        return etree.fromstring(value, parser=parser)
    return value


def _transform_string_or_dom(transform):
    return lambda x: transform(_to_xslt_input(x))


def _format_output(root, to_string, pretty_print=True):
    return etree.tostring(root, pretty_print=pretty_print) if to_string else root


def xslt_transformer_from_file(xslt_filename, *args, **kwargs):
    return xslt_transformer_from_string(
        etree.tostring(etree.parse(xslt_filename)),
        *args, **kwargs
    )


class xslt_transformer_from_string:
    def __init__(self, xslt_template, to_string=True, pretty_print=False):
        self.xslt_template = xslt_template
        self.to_string = to_string
        self.pretty_print = pretty_print
        self.__transform = None
        # validate the XSLT stylesheet
        etree.fromstring(self.xslt_template)

    def _get_transform(self):
        if self.__transform is None:
            # The transform function cannot be pickled and needs to be loaded lazily
            transform = etree.XSLT(etree.fromstring(self.xslt_template))
            self.__transform = transform
        return self.__transform

    def __call__(self, x):
        xslt_input = _to_xslt_input(x)
        LOGGER.debug('xslt_input: %s', xslt_input)
        return _format_output(
            self._get_transform()(xslt_input),
            to_string=self.to_string,
            pretty_print=self.pretty_print
        )
