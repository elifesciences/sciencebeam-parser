import logging
import threading
from typing import Optional

import PIL.Image

from tesserocr import PyTessBaseAPI

from sciencebeam_parser.ocr_models.ocr_model import (
    OpticalCharacterRecognitionModel,
    OpticalCharacterRecognitionModelResult,
    SimpleOpticalCharacterRecognitionModelResult
)


LOGGER = logging.getLogger(__name__)


class TesserComputerVisionModel(OpticalCharacterRecognitionModel):
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self._tesser_api: Optional[PyTessBaseAPI] = None

    @property
    def tesser_api(self) -> PyTessBaseAPI:
        if self._tesser_api is None:
            self._tesser_api = PyTessBaseAPI().__enter__()
        return self._tesser_api

    def predict_single(self, image: PIL.Image.Image) -> OpticalCharacterRecognitionModelResult:
        with self._lock:
            tesser_api = self.tesser_api
            LOGGER.info(
                'setting ocr image: %dx%d (format=%r)',
                image.width, image.height, image.format
            )
            tesser_api.SetImage(image)
            text = self.tesser_api.GetUTF8Text()
            return SimpleOpticalCharacterRecognitionModelResult(
                text=text
            )
