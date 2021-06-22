import logging

from pygrobid.models.name.data import NameDataGenerator
from pygrobid.models.name.extract import NameSemanticExtractor
from pygrobid.models.delft_model import DelftModel


LOGGER = logging.getLogger(__name__)


class NameModel(DelftModel):
    def get_data_generator(self) -> NameDataGenerator:
        return NameDataGenerator()

    def get_semantic_extractor(self) -> NameSemanticExtractor:
        return NameSemanticExtractor()
