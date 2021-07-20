import logging

from pygrobid.models.data import DEFAULT_DOCUMENT_FEATURES_CONTEXT, DocumentFeaturesContext
from pygrobid.models.segmentation.data import SegmentationDataGenerator
from pygrobid.models.model import Model


LOGGER = logging.getLogger(__name__)


class SegmentationModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext = DEFAULT_DOCUMENT_FEATURES_CONTEXT
    ) -> SegmentationDataGenerator:
        return SegmentationDataGenerator(
            document_features_context=document_features_context
        )
