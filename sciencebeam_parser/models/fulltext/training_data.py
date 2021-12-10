import logging

from sciencebeam_parser.models.training_data import (
    NO_NS_TEI_E,
    AbstractTeiTrainingDataGenerator
)


LOGGER = logging.getLogger(__name__)


# based on:
# https://github.com/kermitt2/grobid/blob/0.7.0/grobid-core/src/main/java/org/grobid/core/engines/FullTextParser.java

ROOT_TRAINING_XML_ELEMENT_PATH = ['text']

TRAINING_XML_ELEMENT_PATH_BY_LABEL = {
    '<section>': ROOT_TRAINING_XML_ELEMENT_PATH + ['head'],
    '<paragraph>': ROOT_TRAINING_XML_ELEMENT_PATH + ['p'],
    '<citation_marker>': ROOT_TRAINING_XML_ELEMENT_PATH + ['p', 'ref[@type="biblio"]'],
    '<table_marker>': ROOT_TRAINING_XML_ELEMENT_PATH + ['p', 'ref[@type="table"]'],
    '<equation_marker>': ROOT_TRAINING_XML_ELEMENT_PATH + ['p', 'ref[@type="formula"]']
}


class FullTextTeiTrainingDataGenerator(AbstractTeiTrainingDataGenerator):
    DEFAULT_TEI_FILENAME_SUFFIX = '.fulltext.tei.xml'
    DEFAULT_DATA_FILENAME_SUFFIX = '.fulltext'

    def __init__(self):
        super().__init__(
            root_training_xml_element_path=ROOT_TRAINING_XML_ELEMENT_PATH,
            training_xml_element_path_by_label=TRAINING_XML_ELEMENT_PATH_BY_LABEL,
            element_maker=NO_NS_TEI_E
        )
