import logging

from pygrobid.models.data import DEFAULT_DOCUMENT_FEATURES_CONTEXT, DocumentFeaturesContext
from pygrobid.models.model import Model
from pygrobid.models.fulltext.data import FullTextDataGenerator
from pygrobid.models.figure.extract import FigureSemanticExtractor


LOGGER = logging.getLogger(__name__)


class FigureModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext = DEFAULT_DOCUMENT_FEATURES_CONTEXT
    ) -> FullTextDataGenerator:
        return FullTextDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> FigureSemanticExtractor:
        return FigureSemanticExtractor()
