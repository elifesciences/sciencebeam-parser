from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

import PIL.Image

from sciencebeam_parser.utils.lazy import LazyLoaded, Preloadable


class OpticalCharacterRecognitionModelResult(ABC):
    @abstractmethod
    def get_text(self) -> str:
        pass


@dataclass
class SimpleOpticalCharacterRecognitionModelResult(OpticalCharacterRecognitionModelResult):
    text: str

    def get_text(self) -> str:
        return self.text


class OpticalCharacterRecognitionModel(ABC, Preloadable):
    @abstractmethod
    def predict_single(self, image: PIL.Image.Image) -> OpticalCharacterRecognitionModelResult:
        pass


T_OpticalCharacterRecognitionModelFactory = Callable[[], OpticalCharacterRecognitionModel]


class LazyOpticalCharacterRecognitionModel(OpticalCharacterRecognitionModel):
    def __init__(self, factory: T_OpticalCharacterRecognitionModelFactory) -> None:
        super().__init__()
        self._lazy_model = LazyLoaded[OpticalCharacterRecognitionModel](factory)

    def __repr__(self) -> str:
        return '%s(factory=%r, loaded=%r)' % (
            type(self).__name__, self._lazy_model.factory, self._lazy_model.is_loaded
        )

    @property
    def ocr_model(self) -> OpticalCharacterRecognitionModel:
        return self._lazy_model.get()

    def preload(self):
        self.ocr_model.preload()

    def predict_single(self, image: PIL.Image.Image) -> OpticalCharacterRecognitionModelResult:
        return self.ocr_model.predict_single(image)
