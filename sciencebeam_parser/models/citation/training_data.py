import logging

from sciencebeam_parser.models.training_data import (
    AbstractTeiTrainingDataGenerator
)


LOGGER = logging.getLogger(__name__)


# based on:
# https://github.com/kermitt2/grobid/blob/0.7.0/grobid-core/src/main/java/org/grobid/core/engines/CitationParser.java

ROOT_TRAINING_XML_ELEMENT_PATH = ['text', 'back', 'listBibl', 'bibl']

TRAINING_XML_ELEMENT_PATH_BY_LABEL = {
    '<title>': ROOT_TRAINING_XML_ELEMENT_PATH + ['title[@level="a"]'],
    '<author>': ROOT_TRAINING_XML_ELEMENT_PATH + ['author'],
    '<journal>': ROOT_TRAINING_XML_ELEMENT_PATH + ['title[@level="j"]'],
    '<series>': ROOT_TRAINING_XML_ELEMENT_PATH + ['title[@level="s"]'],
    '<booktitle>': ROOT_TRAINING_XML_ELEMENT_PATH + ['title[@level="m"]'],
    '<date>': ROOT_TRAINING_XML_ELEMENT_PATH + ['date']
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
