import logging

from sciencebeam_parser.models.training_data import (
    AbstractTeiTrainingDataGenerator
)


LOGGER = logging.getLogger(__name__)


# based on:
# https://github.com/kermitt2/grobid/blob/0.7.0/grobid-core/src/main/java/org/grobid/core/engines/AuthorParser.java

ROOT_TRAINING_XML_ELEMENT_PATH = [
    'teiHeader', 'fileDesc', 'sourceDesc', 'biblStruct', 'analytic', 'author', 'persName'
]

TRAINING_XML_ELEMENT_PATH_BY_LABEL = {
    '<marker>': ROOT_TRAINING_XML_ELEMENT_PATH + ['marker'],
    '<title>': ROOT_TRAINING_XML_ELEMENT_PATH + ['roleName'],
    '<forename>': ROOT_TRAINING_XML_ELEMENT_PATH + ['forename'],
    '<middlename>': ROOT_TRAINING_XML_ELEMENT_PATH + ['middlename'],
    '<surname>': ROOT_TRAINING_XML_ELEMENT_PATH + ['surname'],
    '<suffix>': ROOT_TRAINING_XML_ELEMENT_PATH + ['suffix'],
    '<other>': ROOT_TRAINING_XML_ELEMENT_PATH + ['other']
}


class NameTeiTrainingDataGenerator(AbstractTeiTrainingDataGenerator):
    DEFAULT_TEI_FILENAME_SUFFIX = '.headers.authors.tei.xml'

    def __init__(self):
        super().__init__(
            root_training_xml_element_path=ROOT_TRAINING_XML_ELEMENT_PATH,
            training_xml_element_path_by_label=TRAINING_XML_ELEMENT_PATH_BY_LABEL,
            use_tei_namespace=True,
            root_tag='TEI',
            default_tei_filename_suffix=(
                NameTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
            ),
            default_data_filename_suffix=None
        )
