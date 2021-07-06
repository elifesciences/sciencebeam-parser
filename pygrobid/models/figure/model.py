import logging

from pygrobid.models.model import Model
from pygrobid.models.fulltext.data import FullTextDataGenerator
from pygrobid.models.figure.extract import FigureSemanticExtractor


LOGGER = logging.getLogger(__name__)


class FigureModel(Model):
    def get_data_generator(self) -> FullTextDataGenerator:
        return FullTextDataGenerator()

    def get_semantic_extractor(self) -> FigureSemanticExtractor:
        return FigureSemanticExtractor()
