import logging

from pygrobid.models.model import Model
from pygrobid.models.citation.data import CitationDataGenerator
from pygrobid.models.citation.extract import CitationSemanticExtractor


LOGGER = logging.getLogger(__name__)


class CitationModel(Model):
    def get_data_generator(self) -> CitationDataGenerator:
        return CitationDataGenerator()

    def get_semantic_extractor(self) -> CitationSemanticExtractor:
        return CitationSemanticExtractor()
