from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional

import PIL.Image


class OpticalCharacterRecognitionModelResult(ABC):
    @abstractmethod
    def get_text(self) -> str:
        pass


@dataclass
class SimpleOpticalCharacterRecognitionModelResult(OpticalCharacterRecognitionModelResult):
    text: str

    def get_text(self) -> str:
        return self.text


class OpticalCharacterRecognitionModel(ABC):
    @abstractmethod
    def predict_single(self, image: PIL.Image.Image) -> OpticalCharacterRecognitionModelResult:
        pass


T_OpticalCharacterRecognitionModelFactory = Callable[[], OpticalCharacterRecognitionModel]


class LazyOpticalCharacterRecognitionModel(OpticalCharacterRecognitionModel):
    def __init__(self, factory: T_OpticalCharacterRecognitionModelFactory) -> None:
        super().__init__()
        self._factory = factory
        self._ocr_model: Optional[OpticalCharacterRecognitionModel] = None

    @property
    def ocr_model(self) -> OpticalCharacterRecognitionModel:
        if self._ocr_model is None:
            self._ocr_model = self._factory()
        return self._ocr_model

    def predict_single(self, image: PIL.Image.Image) -> OpticalCharacterRecognitionModelResult:
        return self.ocr_model.predict_single(image)
