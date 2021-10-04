import logging
from typing import Optional, Sequence, Tuple

import PIL.Image

from layoutparser.elements.layout import Layout
from layoutparser.models.auto_layoutmodel import AutoLayoutModel
from layoutparser.models.base_layoutmodel import BaseLayoutModel

from sciencebeam_parser.utils.bounding_box import BoundingBox
from sciencebeam_parser.cv_models.cv_model import (
    ComputerVisionModel,
    ComputerVisionModelInstance,
    ComputerVisionModelResult
)


LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = 'lp://efficientdet/PubLayNet'


def load_model(model_path: str) -> BaseLayoutModel:
    LOGGER.info('loading model: %r', model_path)
    return AutoLayoutModel(model_path)


def get_bounding_box_for_layout_parser_coordinates(
    coordinates: Tuple[float, float, float, float]
) -> BoundingBox:
    x1, y1, x2, y2 = coordinates
    return BoundingBox(x=x1, y=y1, width=x2 - x1, height=y2 - y1)


class LayoutParserComputerVisionModelInstance(ComputerVisionModelInstance):
    def __init__(self, bounding_box: BoundingBox):
        super().__init__()
        self.bounding_box = bounding_box

    def get_bounding_box(self) -> BoundingBox:
        return self.bounding_box


class LayoutParserComputerVisionModelResult(ComputerVisionModelResult):
    def __init__(self, layout: Layout):
        super().__init__()
        self.layout = layout

    def get_instances_by_type_name(self, type_name: str) -> Sequence[ComputerVisionModelInstance]:
        return [
            LayoutParserComputerVisionModelInstance(
                get_bounding_box_for_layout_parser_coordinates(block.coordinates)
            )
            for block in self.layout
            if block.type == type_name
        ]


class LayoutParserComputerVisionModel(ComputerVisionModel):
    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        super().__init__()
        self.model_path = model_path
        self._layout_model: Optional[BaseLayoutModel] = None

    @property
    def layout_model(self) -> BaseLayoutModel:
        if self._layout_model is None:
            self._layout_model = load_model(self.model_path)
        return self._layout_model

    def predict_single(self, image: PIL.Image.Image) -> ComputerVisionModelResult:
        return LayoutParserComputerVisionModelResult(
            self.layout_model.detect(image)
        )
