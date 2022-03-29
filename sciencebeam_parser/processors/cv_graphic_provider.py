import os
import logging
from time import monotonic
from typing import Dict, Iterable, Mapping, Optional, Sequence, Set

import PIL.Image

from sciencebeam_parser.utils.bounding_box import BoundingBox
from sciencebeam_parser.document.semantic_document import SemanticGraphic
from sciencebeam_parser.document.layout_document import (
    DEFAULT_LAYOUT_PAGE_META,
    LayoutDocument,
    LayoutGraphic,
    LayoutPage,
    LayoutPageCoordinates
)
from sciencebeam_parser.cv_models.cv_model import ComputerVisionModel
from sciencebeam_parser.processors.document_page_image import DocumentPageImage
from sciencebeam_parser.processors.graphic_provider import (
    DocumentGraphicProvider,
    get_semantic_graphic_for_layout_graphic,
    get_semantic_graphic_list_for_layout_graphic_list
)


LOGGER = logging.getLogger(__name__)


def get_cropped_image(image: PIL.Image.Image, bounding_box: BoundingBox) -> PIL.Image.Image:
    return image.crop((
        bounding_box.x,
        bounding_box.y,
        bounding_box.right,
        bounding_box.bottom
    ))


def get_bounding_box_intersection_area_ratio(
    bounding_box_1: BoundingBox,
    bounding_box_2: BoundingBox,
    empty_ratio: float = 0.0
) -> float:
    max_area = max(bounding_box_1.area, bounding_box_2.area)
    if not max_area:
        return empty_ratio
    intersection_area = bounding_box_1.intersection(bounding_box_2).area
    return intersection_area / max_area


def get_layout_graphic_with_similar_coordinates(
    page_graphics: Sequence[LayoutGraphic],
    bounding_box: BoundingBox,
    threshold: float = 0.80,
    ignored_graphic_types: Set[str] = None
) -> Optional[LayoutGraphic]:
    sorted_area_intersection_bounding_boxes = sorted((
        (
            get_bounding_box_intersection_area_ratio(
                bounding_box,
                graphic.coordinates.bounding_box
            ),
            graphic
        )
        for graphic in page_graphics
        if graphic.coordinates and (
            not ignored_graphic_types or graphic.graphic_type not in ignored_graphic_types
        )
    ), key=lambda t: -t[0])
    if not sorted_area_intersection_bounding_boxes:
        return None
    LOGGER.debug(
        'sorted_area_intersection_bounding_boxes: %r',
        sorted_area_intersection_bounding_boxes
    )
    best_area_ratio, best_matching_graphic = sorted_area_intersection_bounding_boxes[0]
    if best_area_ratio < threshold:
        LOGGER.debug('best_area_ratio below threshold: %.3f < %.3f', best_area_ratio, threshold)
        return None
    return best_matching_graphic


class ComputerVisionDocumentGraphicProvider(DocumentGraphicProvider):
    def __init__(
        self,
        computer_vision_model: ComputerVisionModel,
        page_image_iterable: Iterable[DocumentPageImage],
        temp_dir: str
    ):
        super().__init__()
        self.computer_vision_model = computer_vision_model
        self.page_image_iterable = page_image_iterable
        self.temp_dir = temp_dir
        # ignoring svg for now because we are also ignoring it when matching graphics
        # an svg image may also not be standalone and require text to be complete
        self.ignored_graphic_types = {'svg'}

    def iter_semantic_graphic_for_image(  # pylint: disable=too-many-locals
        self,
        image: PIL.Image.Image,
        extract_graphic_assets: bool,
        page_number: int,
        page: Optional[LayoutPage]
    ) -> Iterable[SemanticGraphic]:
        LOGGER.debug('image size: %d x %d', image.width, image.height)
        page_meta = page.meta if page is not None else DEFAULT_LAYOUT_PAGE_META
        page_coordinates = (
            page.meta.coordinates if page is not None else None
        )
        page_graphics = (
            page.graphics if page is not None else []
        )
        cv_start = monotonic()
        cv_result = self.computer_vision_model.predict_single(image)
        cv_end = monotonic()
        cv_instances = cv_result.get_instances_by_type_names(['Figure', 'Table'])
        cv_type_name_and_coordinates_list = [
            (instance.get_type_name(), instance.get_bounding_box())
            for instance in cv_instances
        ]
        LOGGER.info(
            (
                'cv result, took=%.3fs, page_number=%d, image_size=%dx%d'
                ', cv_type_name_and_coordinates_list=%r'
            ),
            cv_end - cv_start,
            page_number,
            image.width,
            image.height,
            cv_type_name_and_coordinates_list
        )
        count_by_type_name_map: Dict[str, int] = {}
        for type_name, cv_coordinates in cv_type_name_and_coordinates_list:
            lower_type_name = type_name.lower()
            count_by_type_name_map[type_name] = count_by_type_name_map.get(type_name, 0) + 1
            item_number = count_by_type_name_map[type_name]
            local_image_path: Optional[str] = None
            relative_image_path: Optional[str] = None
            scaled_item_coordinates = cv_coordinates
            if page_coordinates:
                scaled_item_coordinates = (
                    cv_coordinates
                    .scale_by(
                        page_coordinates.width / image.width,
                        page_coordinates.height / image.height
                    )
                )
            matching_layout_graphic = get_layout_graphic_with_similar_coordinates(
                page_graphics=page_graphics,
                bounding_box=scaled_item_coordinates,
                ignored_graphic_types=self.ignored_graphic_types
            )
            if matching_layout_graphic is not None:
                yield get_semantic_graphic_for_layout_graphic(
                    matching_layout_graphic,
                    extract_graphic_assets=extract_graphic_assets
                )
                continue
            if extract_graphic_assets:
                local_image_path = os.path.join(
                    self.temp_dir, f'{lower_type_name}-{page_number}-{item_number}.png'
                )
                relative_image_path = os.path.basename(local_image_path)
                cropped_image = get_cropped_image(image, cv_coordinates)
                cropped_image.save(local_image_path)
            layout_graphic = LayoutGraphic(
                coordinates=LayoutPageCoordinates(
                    x=scaled_item_coordinates.x,
                    y=scaled_item_coordinates.y,
                    width=scaled_item_coordinates.width,
                    height=scaled_item_coordinates.height,
                    page_number=page_number
                ),
                page_meta=page_meta,
                graphic_type=f'cv-{lower_type_name}',
                local_file_path=local_image_path
            )
            semantic_graphic = SemanticGraphic(
                layout_graphic=layout_graphic,
                relative_path=relative_image_path
            )
            yield semantic_graphic

    def get_page_by_page_number_map(
        self,
        layout_document: LayoutDocument
    ) -> Mapping[int, Optional[LayoutPage]]:
        return {
            page.meta.page_number: page
            for page in layout_document.pages
        }

    def iter_semantic_graphic_for_layout_document(
        self,
        layout_document: LayoutDocument,
        extract_graphic_assets: bool
    ) -> Iterable[SemanticGraphic]:
        page_by_page_number_map = self.get_page_by_page_number_map(
            layout_document
        )
        LOGGER.debug(
            'cv model: page_by_page_number_map=%r',
            page_by_page_number_map
        )
        has_cv_semantic_graphic: bool = False
        for page_image in self.page_image_iterable:
            LOGGER.debug('page_image: %r', page_image)
            page_number = page_image.page_number
            with PIL.Image.open(page_image.page_image_path) as image:
                for semantic_graphic in self.iter_semantic_graphic_for_image(
                    image,
                    extract_graphic_assets=extract_graphic_assets,
                    page_number=page_number,
                    page=page_by_page_number_map.get(page_number)
                ):
                    has_cv_semantic_graphic = True
                    yield semantic_graphic
        if not has_cv_semantic_graphic:
            LOGGER.info('no graphics detected using cv model, falling back to regular graphics')
            yield from get_semantic_graphic_list_for_layout_graphic_list(
                layout_document.iter_all_graphics(),
                extract_graphic_assets=extract_graphic_assets
            )
