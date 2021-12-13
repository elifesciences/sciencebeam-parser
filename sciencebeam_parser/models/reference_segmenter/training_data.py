import logging

from sciencebeam_parser.models.training_data import (
    NO_NS_TEI_E,
    AbstractTeiTrainingDataGenerator
)


LOGGER = logging.getLogger(__name__)


# based on:
# https://github.com/kermitt2/grobid/blob/0.7.0/grobid-core/src/main/java/org/grobid/core/engines/ReferenceSegmenterParser.java

ROOT_TRAINING_XML_ELEMENT_PATH = ['text', 'listBibl']

TRAINING_XML_ELEMENT_PATH_BY_LABEL = {
    '<reference>': ROOT_TRAINING_XML_ELEMENT_PATH + ['bibl'],
    '<label>': ROOT_TRAINING_XML_ELEMENT_PATH + ['bibl', 'label']
}


class ReferenceSegmenterTeiTrainingDataGenerator(AbstractTeiTrainingDataGenerator):
    DEFAULT_TEI_FILENAME_SUFFIX = '.referenceSegmenter.tei.xml'
    DEFAULT_DATA_FILENAME_SUFFIX = '.referenceSegmenter'

    def __init__(self):
        super().__init__(
            root_training_xml_element_path=ROOT_TRAINING_XML_ELEMENT_PATH,
            training_xml_element_path_by_label=TRAINING_XML_ELEMENT_PATH_BY_LABEL,
            element_maker=NO_NS_TEI_E
        )
