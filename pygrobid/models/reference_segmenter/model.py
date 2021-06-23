import logging

from pygrobid.models.delft_model import DelftModel
from pygrobid.models.reference_segmenter.data import ReferenceSegmenterDataGenerator
from pygrobid.models.reference_segmenter.extract import ReferenceSegmenterSemanticExtractor


LOGGER = logging.getLogger(__name__)


class ReferenceSegmenterModel(DelftModel):
    def get_data_generator(self) -> ReferenceSegmenterDataGenerator:
        return ReferenceSegmenterDataGenerator()

    def get_semantic_extractor(self) -> ReferenceSegmenterSemanticExtractor:
        return ReferenceSegmenterSemanticExtractor()
