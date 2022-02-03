import logging

from sciencebeam_parser.models.data import (
    DocumentFeaturesContext
)
from sciencebeam_parser.models.figure.training_data import (
    FigureTeiTrainingDataGenerator,
    FigureTrainingTeiParser
)
from sciencebeam_parser.models.model import Model
from sciencebeam_parser.models.fulltext.data import FullTextDataGenerator
from sciencebeam_parser.models.figure.extract import FigureSemanticExtractor


LOGGER = logging.getLogger(__name__)


class FigureModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext
    ) -> FullTextDataGenerator:
        return FullTextDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> FigureSemanticExtractor:
        return FigureSemanticExtractor()

    def get_tei_training_data_generator(self) -> FigureTeiTrainingDataGenerator:
        return FigureTeiTrainingDataGenerator()

    def get_training_tei_parser(self) -> FigureTrainingTeiParser:
        return FigureTrainingTeiParser()
