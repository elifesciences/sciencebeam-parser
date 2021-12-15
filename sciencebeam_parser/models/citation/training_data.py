import logging

from lxml import etree

from sciencebeam_parser.document.layout_document import LayoutBlock
from sciencebeam_parser.document.tei.common import tei_xpath
from sciencebeam_parser.models.training_data import (
    AbstractTeiTrainingDataGenerator
)
from sciencebeam_parser.models.citation.extract import (
    parse_pubnum
)
from sciencebeam_parser.utils.xml import get_text_content


LOGGER = logging.getLogger(__name__)


# based on:
# https://github.com/kermitt2/grobid/blob/0.7.0/grobid-core/src/main/java/org/grobid/core/engines/CitationParser.java

ROOT_TRAINING_XML_ELEMENT_PATH = ['text', 'back', 'listBibl', 'bibl']

TRAINING_XML_ELEMENT_PATH_BY_LABEL = {
    '<title>': ROOT_TRAINING_XML_ELEMENT_PATH + ['title[@level="a"]'],
    '<author>': ROOT_TRAINING_XML_ELEMENT_PATH + ['author'],
    '<editor>': ROOT_TRAINING_XML_ELEMENT_PATH + ['editor'],
    '<institution>': ROOT_TRAINING_XML_ELEMENT_PATH + ['orgName'],
    '<collaboration>': ROOT_TRAINING_XML_ELEMENT_PATH + ['orgName[@type="collaboration"]'],
    '<journal>': ROOT_TRAINING_XML_ELEMENT_PATH + ['title[@level="j"]'],
    '<series>': ROOT_TRAINING_XML_ELEMENT_PATH + ['title[@level="s"]'],
    '<booktitle>': ROOT_TRAINING_XML_ELEMENT_PATH + ['title[@level="m"]'],
    '<date>': ROOT_TRAINING_XML_ELEMENT_PATH + ['date'],
    '<volume>': ROOT_TRAINING_XML_ELEMENT_PATH + ['biblScope[@unit="volume"]'],
    '<issue>': ROOT_TRAINING_XML_ELEMENT_PATH + ['biblScope[@unit="issue"]'],
    '<pages>': ROOT_TRAINING_XML_ELEMENT_PATH + ['biblScope[@unit="page"]'],
    '<publisher>': ROOT_TRAINING_XML_ELEMENT_PATH + ['publisher'],
    '<location>': ROOT_TRAINING_XML_ELEMENT_PATH + ['pubPlace'],
    '<tech>': ROOT_TRAINING_XML_ELEMENT_PATH + ['note[@type="report"]'],
    '<web>': ROOT_TRAINING_XML_ELEMENT_PATH + ['ptr[@type="web"]'],
    '<pubnum>': ROOT_TRAINING_XML_ELEMENT_PATH + ['idno'],
    '<note>': ROOT_TRAINING_XML_ELEMENT_PATH + ['note']
}


class CitationTeiTrainingDataGenerator(AbstractTeiTrainingDataGenerator):
    DEFAULT_TEI_FILENAME_SUFFIX = '.references.tei.xml'
    DEFAULT_DATA_FILENAME_SUFFIX = '.references'

    def __init__(self):
        super().__init__(
            root_training_xml_element_path=ROOT_TRAINING_XML_ELEMENT_PATH,
            training_xml_element_path_by_label=TRAINING_XML_ELEMENT_PATH_BY_LABEL,
            use_tei_namespace=True,
            root_tag='TEI'
        )

    def get_post_processed_xml_root(self, xml_root: etree.ElementBase):
        for idno_element in tei_xpath(xml_root, '//tei:idno'):
            semantic_external_identifier = parse_pubnum(LayoutBlock.for_text(
                get_text_content(idno_element)
            ))
            external_identifier_type = semantic_external_identifier.external_identifier_type
            if not external_identifier_type:
                continue
            idno_element.attrib['type'] = external_identifier_type
        return xml_root
