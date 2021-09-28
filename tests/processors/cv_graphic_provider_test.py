import os
from pathlib import Path
from typing import Optional, Sequence
from unittest.mock import MagicMock

import pytest
import PIL.Image

from sciencebeam_parser.utils.bounding_box import BoundingBox
from sciencebeam_parser.document.layout_document import (
    LOGGER,
    LayoutDocument,
    LayoutGraphic,
    LayoutPage,
    LayoutPageCoordinates,
    LayoutPageMeta
)
from sciencebeam_parser.cv_models.cv_model import (
    SimpleComputerVisionModelInstance
)
from sciencebeam_parser.processors.document_page_image import DocumentPageImage
from sciencebeam_parser.processors.cv_graphic_provider import (
    ComputerVisionDocumentGraphicProvider,
    get_layout_graphic_with_similar_coordinates
)


BOUNDING_BOX_1 = BoundingBox(x=10, y=10, width=10, height=100)


@pytest.fixture(name='computer_vision_model_mock')
def _computer_vision_model_mock() -> MagicMock:
    return MagicMock(name='computer_vision_model')


def _create_page(
    coordinates: LayoutPageCoordinates,
    graphics: Optional[Sequence[LayoutGraphic]] = None
) -> LayoutPage:
    return LayoutPage(
        meta=LayoutPageMeta(
            page_number=coordinates.page_number,
            coordinates=coordinates
        ),
        blocks=[],
        graphics=graphics or []
    )


class TestGetLayoutGraphicWithSimilarCoordinates:
    def test_should_return_the_best_matching_graphic(
        self
    ):
        page_graphics = [
            LayoutGraphic(coordinates=LayoutPageCoordinates(
                x=10, y=10, width=200, height=100
            )),
            LayoutGraphic(coordinates=LayoutPageCoordinates(
                x=10, y=10, width=100, height=100
            )),
            LayoutGraphic(coordinates=LayoutPageCoordinates(
                x=100, y=10, width=100, height=100
            )),
        ]
        result = get_layout_graphic_with_similar_coordinates(
            page_graphics,
            BoundingBox(x=10, y=10, width=90, height=100)
        )
        assert result == page_graphics[1]

    def test_should_ignore_matches_below_threshold(
        self
    ):
        page_graphics = [
            LayoutGraphic(coordinates=LayoutPageCoordinates(
                x=10, y=10, width=100, height=100
            ))
        ]
        result = get_layout_graphic_with_similar_coordinates(
            page_graphics,
            BoundingBox(x=10, y=10, width=10, height=1000)
        )
        assert result is None

    def test_should_ignore_graphics_without_coordinates(
        self
    ):
        page_graphics = [
            LayoutGraphic(coordinates=None)
        ]
        result = get_layout_graphic_with_similar_coordinates(
            page_graphics,
            BoundingBox(x=10, y=10, width=10, height=1000)
        )
        assert result is None

    def test_should_ignore_svg_graphics(
        self
    ):
        page_graphics = [
            LayoutGraphic(coordinates=LayoutPageCoordinates.from_bounding_box(
                BOUNDING_BOX_1
            ), graphic_type='svg')
        ]
        result = get_layout_graphic_with_similar_coordinates(
            page_graphics,
            BOUNDING_BOX_1,
            ignored_graphic_types={'svg'}
        )
        assert result is None


class TestComputerVisionDocumentGraphicProvider:
    @pytest.mark.parametrize(
        "extract_graphic_assets", (True, False)
    )
    def test_should_find_bbox_and_map_to_page_coordinates(  # pylint: disable=too-many-locals
        self,
        computer_vision_model_mock: MagicMock,
        tmp_path: Path,
        extract_graphic_assets: bool
    ):
        image_path = tmp_path / 'page10.png'
        image = PIL.Image.new('RGB', size=(20, 10), color=(255, 0, 0))
        image.save(image_path)
        page_images = [DocumentPageImage(
            page_number=10,
            page_image_path=str(image_path)
        )]
        layout_document = LayoutDocument(pages=[
            _create_page(
                coordinates=LayoutPageCoordinates(
                    x=0, y=0, width=200, height=100, page_number=10
                )
            )
        ])
        cv_result = computer_vision_model_mock.predict_single.return_value
        cv_bbox = BoundingBox(x=1, y=2, width=3, height=4)
        cv_result.get_instances_by_type_name.return_value = [
            SimpleComputerVisionModelInstance(bounding_box=cv_bbox)
        ]
        expected_page_coordinates = LayoutPageCoordinates(
            x=10, y=20, width=30, height=40, page_number=10
        )
        graphic_provider = ComputerVisionDocumentGraphicProvider(
            computer_vision_model=computer_vision_model_mock,
            page_image_iterable=page_images,
            temp_dir=str(tmp_path)
        )
        semantic_graphic_list = list(graphic_provider.iter_semantic_graphic_for_layout_document(
            layout_document=layout_document,
            extract_graphic_assets=extract_graphic_assets
        ))
        assert semantic_graphic_list
        semantic_graphic = semantic_graphic_list[0]
        LOGGER.debug('semantic_graphic: %s', semantic_graphic)
        layout_graphic = semantic_graphic.layout_graphic
        assert layout_graphic is not None
        assert layout_graphic.coordinates == expected_page_coordinates
        if extract_graphic_assets:
            assert layout_graphic.local_file_path
            assert (
                semantic_graphic.relative_path
                == os.path.basename(layout_graphic.local_file_path)
            )
            with PIL.Image.open(layout_graphic.local_file_path) as cropped_image:
                assert cropped_image.width == cv_bbox.width
                assert cropped_image.height == cv_bbox.height
        else:
            assert not semantic_graphic.relative_path

    def test_should_prefer_embedded_graphic(  # pylint: disable=too-many-locals
        self,
        computer_vision_model_mock: MagicMock,
        tmp_path: Path
    ):
        image_path = tmp_path / 'page10.png'
        image = PIL.Image.new('RGB', size=(20, 10), color=(255, 0, 0))
        image.save(image_path)
        page_images = [DocumentPageImage(
            page_number=10,
            page_image_path=str(image_path)
        )]
        embedded_graphic = LayoutGraphic(
            coordinates=LayoutPageCoordinates(
                x=10, y=20, width=30, height=40, page_number=10
            )
        )
        layout_document = LayoutDocument(pages=[
            _create_page(
                coordinates=LayoutPageCoordinates(
                    x=0, y=0, width=200, height=100, page_number=10
                ),
                graphics=[embedded_graphic]
            )
        ])
        cv_result = computer_vision_model_mock.predict_single.return_value
        cv_bbox = BoundingBox(x=1, y=2, width=3, height=4)
        cv_result.get_instances_by_type_name.return_value = [
            SimpleComputerVisionModelInstance(bounding_box=cv_bbox)
        ]
        graphic_provider = ComputerVisionDocumentGraphicProvider(
            computer_vision_model=computer_vision_model_mock,
            page_image_iterable=page_images,
            temp_dir=str(tmp_path)
        )
        semantic_graphic_list = list(graphic_provider.iter_semantic_graphic_for_layout_document(
            layout_document=layout_document,
            extract_graphic_assets=True
        ))
        assert semantic_graphic_list
        semantic_graphic = semantic_graphic_list[0]
        LOGGER.debug('semantic_graphic: %s', semantic_graphic)
        assert semantic_graphic.layout_graphic == embedded_graphic
