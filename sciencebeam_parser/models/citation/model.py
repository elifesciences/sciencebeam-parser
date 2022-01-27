import logging
from sciencebeam_parser.models.citation.training_data import (
    CitationTeiTrainingDataGenerator,
    CitationTrainingTeiParser
)

from sciencebeam_parser.models.data import (
    DocumentFeaturesContext
)
from sciencebeam_parser.models.model import Model
from sciencebeam_parser.models.citation.data import CitationDataGenerator
from sciencebeam_parser.models.citation.extract import CitationSemanticExtractor


LOGGER = logging.getLogger(__name__)


class CitationModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext
    ) -> CitationDataGenerator:
        return CitationDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> CitationSemanticExtractor:
        return CitationSemanticExtractor()

    def get_tei_training_data_generator(self) -> CitationTeiTrainingDataGenerator:
        return CitationTeiTrainingDataGenerator()

    def get_training_tei_parser(self) -> CitationTrainingTeiParser:
        return CitationTrainingTeiParser()
