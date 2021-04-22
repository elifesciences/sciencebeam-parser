import logging
from typing import Optional, Iterable, List

from sciencebeam_trainer_delft.sequence_labelling.wrapper import Sequence

from pygrobid.models.segmentation.data import SegmentationDataGenerator
from pygrobid.models.model import Model


LOGGER = logging.getLogger(__name__)


class SegmentationModel(Model):
    def __init__(self, model_url: str):
        self.model_url = model_url
        self._model: Optional[Sequence] = None

    def get_data_generator(self) -> SegmentationDataGenerator:
        return SegmentationDataGenerator()

    @property
    def model(self) -> Sequence:
        if self._model is not None:
            return self._model
        model = Sequence('dummy-model')
        model.load_from(self.model_url)
        self._model = model
        return model

    def predict_labels(
        self,
        texts: List[List[str]],
        features: List[List[List[str]]],
        output_format: Optional[str] = None
    ) -> Iterable[str]:
        model = self.model
        return model.tag(texts, features=features, output_format=output_format)
