import logging

from pygrobid.models.data import DEFAULT_DOCUMENT_FEATURES_CONTEXT, DocumentFeaturesContext
from pygrobid.models.model import Model
from pygrobid.models.citation.data import CitationDataGenerator
from pygrobid.models.citation.extract import CitationSemanticExtractor


LOGGER = logging.getLogger(__name__)


class CitationModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext = DEFAULT_DOCUMENT_FEATURES_CONTEXT
    ) -> CitationDataGenerator:
        return CitationDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> CitationSemanticExtractor:
        return CitationSemanticExtractor()
