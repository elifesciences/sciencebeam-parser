import logging

from pygrobid.models.model import Model
from pygrobid.models.figure.data import FigureDataGenerator
from pygrobid.models.figure.extract import FigureSemanticExtractor


LOGGER = logging.getLogger(__name__)


class FigureModel(Model):
    def get_data_generator(self) -> FigureDataGenerator:
        return FigureDataGenerator()

    def get_semantic_extractor(self) -> FigureSemanticExtractor:
        return FigureSemanticExtractor()
