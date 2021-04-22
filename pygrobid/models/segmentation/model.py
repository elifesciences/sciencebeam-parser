import logging

from pygrobid.models.segmentation.data import SegmentationDataGenerator
from pygrobid.models.delft_model import DelftModel


LOGGER = logging.getLogger(__name__)


class SegmentationModel(DelftModel):
    def get_data_generator(self) -> SegmentationDataGenerator:
        return SegmentationDataGenerator()
