import logging

from sciencebeam_parser.models.data import (
    DEFAULT_DOCUMENT_FEATURES_CONTEXT,
    DocumentFeaturesContext
)
from sciencebeam_parser.models.segmentation.data import SegmentationDataGenerator
from sciencebeam_parser.models.model import Model


LOGGER = logging.getLogger(__name__)


class SegmentationModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext = DEFAULT_DOCUMENT_FEATURES_CONTEXT
    ) -> SegmentationDataGenerator:
        return SegmentationDataGenerator(
            document_features_context=document_features_context
        )
