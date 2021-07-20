import logging

from pygrobid.models.data import DEFAULT_DOCUMENT_FEATURES_CONTEXT, DocumentFeaturesContext
from pygrobid.models.model import Model
from pygrobid.models.reference_segmenter.data import ReferenceSegmenterDataGenerator
from pygrobid.models.reference_segmenter.extract import ReferenceSegmenterSemanticExtractor


LOGGER = logging.getLogger(__name__)


class ReferenceSegmenterModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext = DEFAULT_DOCUMENT_FEATURES_CONTEXT
    ) -> ReferenceSegmenterDataGenerator:
        return ReferenceSegmenterDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> ReferenceSegmenterSemanticExtractor:
        return ReferenceSegmenterSemanticExtractor()
