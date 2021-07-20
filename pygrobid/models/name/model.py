import logging

from pygrobid.models.data import DEFAULT_DOCUMENT_FEATURES_CONTEXT, DocumentFeaturesContext
from pygrobid.models.name.data import NameDataGenerator
from pygrobid.models.name.extract import NameSemanticExtractor
from pygrobid.models.model import Model


LOGGER = logging.getLogger(__name__)


class NameModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext = DEFAULT_DOCUMENT_FEATURES_CONTEXT
    ) -> NameDataGenerator:
        return NameDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> NameSemanticExtractor:
        return NameSemanticExtractor()
