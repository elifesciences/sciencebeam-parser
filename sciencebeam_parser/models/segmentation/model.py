import logging

from sciencebeam_parser.models.data import (
    DocumentFeaturesContext
)
from sciencebeam_parser.models.segmentation.data import SegmentationDataGenerator
from sciencebeam_parser.models.model import Model


LOGGER = logging.getLogger(__name__)


class SegmentationModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext
    ) -> SegmentationDataGenerator:
        return SegmentationDataGenerator(
            document_features_context=document_features_context,
            use_first_token_of_block=(
                self.model_config.get('use_first_token_of_block', True)
            )
        )
