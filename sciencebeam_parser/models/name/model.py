import logging

from sciencebeam_parser.models.data import (
    DocumentFeaturesContext
)
from sciencebeam_parser.models.name.data import NameDataGenerator
from sciencebeam_parser.models.name.extract import NameSemanticExtractor
from sciencebeam_parser.models.model import Model


LOGGER = logging.getLogger(__name__)


class NameModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext
    ) -> NameDataGenerator:
        return NameDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> NameSemanticExtractor:
        return NameSemanticExtractor()
