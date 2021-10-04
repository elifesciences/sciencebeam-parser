from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import PIL.Image

from sciencebeam_parser.utils.bounding_box import BoundingBox


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


class ComputerVisionModel(ABC):
    @abstractmethod
    def predict_single(self, image: PIL.Image.Image) -> ComputerVisionModelResult:
        pass


T_ComputerVisionModelFactory = Callable[[], ComputerVisionModel]


class LazyComputerVisionModel(ComputerVisionModel):
    def __init__(self, factory: T_ComputerVisionModelFactory) -> None:
        super().__init__()
        self._factory = factory
        self._cv_model: Optional[ComputerVisionModel] = None

    @property
    def cv_model(self) -> ComputerVisionModel:
        if self._cv_model is None:
            self._cv_model = self._factory()
        return self._cv_model

    def predict_single(self, image: PIL.Image.Image) -> ComputerVisionModelResult:
        return self.cv_model.predict_single(image)
