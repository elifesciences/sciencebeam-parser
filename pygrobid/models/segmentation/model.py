import logging

from pygrobid.models.segmentation.data import SegmentationDataGenerator
from pygrobid.models.model import Model


LOGGER = logging.getLogger(__name__)


class SegmentationModel(Model):
    def get_data_generator(self) -> SegmentationDataGenerator:
        return SegmentationDataGenerator()
