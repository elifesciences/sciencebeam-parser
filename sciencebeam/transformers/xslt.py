import six
import lxml.etree as ET


def _parse_if_string(x):
    return ET.fromstring(x) if isinstance(x, six.string_types) else x


def _transform_string_or_dom(transform):
    return lambda x: transform(_parse_if_string(x))


def _format_output(root, to_string, pretty_print=True):
    return ET.tostring(root, pretty_print=pretty_print) if to_string else root


def xslt_transformer_from_file(xslt_filename, *args, **kwargs):
    return xslt_transformer_from_string(
        ET.tostring(ET.parse(xslt_filename)),
        *args, **kwargs
    )


class xslt_transformer_from_string:
    def __init__(self, xslt_template, to_string=True, pretty_print=False):
        self.xslt_template = xslt_template
        self.to_string = to_string
        self.pretty_print = pretty_print
        self.__transform = None
        # validate the XSLT stylesheet
        ET.fromstring(self.xslt_template)

    def _get_transform(self):
        if self.__transform is None:
            # The transform function cannot be pickled and needs to be loaded lazily
            transform = ET.XSLT(ET.fromstring(self.xslt_template))
            self.__transform = transform
        return self.__transform

    def __call__(self, x):
        return _format_output(
            self._get_transform()(_parse_if_string(x)),
            to_string=self.to_string,
            pretty_print=self.pretty_print
        )
