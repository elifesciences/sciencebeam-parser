import logging

from lxml import etree

from pygrobid.utils.xml import get_text_content
from pygrobid.lookup.country import CountryLookUp, SimpleCountryLookUp


LOGGER = logging.getLogger(__name__)


TEI_NS = 'http://www.tei-c.org/ns/1.0'
TEI_NS_PREFIX = '{%s}' % TEI_NS

TEI_NS_MAP = {
    'tei': TEI_NS
}

TEI_CELL = TEI_NS_PREFIX + 'cell'


def load_xml_country_lookup_from_file(
    filename: str
) -> CountryLookUp:
    root = etree.parse(filename)
    valid_country_texts = {
        get_text_content(node)
        for node in root.xpath('//tei:cell', namespaces=TEI_NS_MAP)
    }
    LOGGER.debug('valid_country_texts: %s', valid_country_texts)
    return SimpleCountryLookUp(valid_country_texts)
