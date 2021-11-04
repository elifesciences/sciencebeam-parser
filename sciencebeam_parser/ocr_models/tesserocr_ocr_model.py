import logging
import threading
from typing import Optional, Union

import PIL.Image

import tesserocr
from tesserocr import PyTessBaseAPI

from sciencebeam_parser.ocr_models.ocr_model import (
    OpticalCharacterRecognitionModel,
    OpticalCharacterRecognitionModelResult,
    SimpleOpticalCharacterRecognitionModelResult
)
from sciencebeam_parser.utils.lazy import LazyLoaded


LOGGER = logging.getLogger(__name__)


DEFAULT_OCR_LANG = 'eng'


def get_enum_value(enum_class, value: Optional[Union[int, str]], default_value: int) -> int:
    if value is None:
        return default_value
    if isinstance(value, int):
        return value
    return getattr(enum_class, value)


class TesserComputerVisionModel(OpticalCharacterRecognitionModel):
    def __init__(self, config: dict):
        super().__init__()
        self._lock = threading.Lock()
        self.lang = str(config.get('lang') or DEFAULT_OCR_LANG)
        self.oem = get_enum_value(tesserocr.OEM, config.get('oem'), tesserocr.OEM.DEFAULT)
        self.psm = get_enum_value(tesserocr.PSM, config.get('psm'), tesserocr.PSM.AUTO)
        self._lazy_tesser_api = LazyLoaded[PyTessBaseAPI](self._create_tesser_api)

    def _create_tesser_api(self) -> PyTessBaseAPI:
        LOGGER.info(
            'creating tesser api with oem=%r, psm=%r, lang=%r',
            self.oem, self.psm, self.lang
        )
        return PyTessBaseAPI(
            oem=self.oem,
            psm=self.psm,
            lang=self.lang
        ).__enter__()

    @property
    def tesser_api(self) -> PyTessBaseAPI:
        return self._lazy_tesser_api.get()

    def preload(self):
        with self._lock:
            self._lazy_tesser_api.get()

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
