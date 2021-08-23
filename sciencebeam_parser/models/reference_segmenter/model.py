import logging

from sciencebeam_parser.models.data import (
    DocumentFeaturesContext
)
from sciencebeam_parser.models.model import Model
from sciencebeam_parser.models.reference_segmenter.data import ReferenceSegmenterDataGenerator
from sciencebeam_parser.models.reference_segmenter.extract import (
    ReferenceSegmenterSemanticExtractor
)


LOGGER = logging.getLogger(__name__)


class ReferenceSegmenterModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext
    ) -> ReferenceSegmenterDataGenerator:
        return ReferenceSegmenterDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> ReferenceSegmenterSemanticExtractor:
        return ReferenceSegmenterSemanticExtractor()
