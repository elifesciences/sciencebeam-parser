from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Sequence

import PIL.Image

from sciencebeam_parser.utils.bounding_box import BoundingBox
from sciencebeam_parser.utils.lazy import LazyLoaded, Preloadable


class ComputerVisionModelInstance(ABC):
    @abstractmethod
    def get_bounding_box(self) -> BoundingBox:
        pass


@dataclass
class SimpleComputerVisionModelInstance(ComputerVisionModelInstance):
    bounding_box: BoundingBox

    def get_bounding_box(self) -> BoundingBox:
        return self.bounding_box


class ComputerVisionModelResult(ABC):
    @abstractmethod
    def get_instances_by_type_name(self, type_name: str) -> Sequence[ComputerVisionModelInstance]:
        pass


class ComputerVisionModel(ABC, Preloadable):
    @abstractmethod
    def predict_single(self, image: PIL.Image.Image) -> ComputerVisionModelResult:
        pass


T_ComputerVisionModelFactory = Callable[[], ComputerVisionModel]


class LazyComputerVisionModel(ComputerVisionModel):
    def __init__(self, factory: T_ComputerVisionModelFactory) -> None:
        super().__init__()
        self._lazy_model = LazyLoaded[ComputerVisionModel](factory)

    def __repr__(self) -> str:
        return '%s(factory=%r, loaded=%r)' % (
            type(self).__name__, self._lazy_model.factory, self._lazy_model.is_loaded
        )

    @property
    def cv_model(self) -> ComputerVisionModel:
        return self._lazy_model.get()

    def preload(self):
        self.cv_model.preload()

    def predict_single(self, image: PIL.Image.Image) -> ComputerVisionModelResult:
        return self.cv_model.predict_single(image)
