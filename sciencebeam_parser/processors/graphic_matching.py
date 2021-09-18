import logging
import math
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, NamedTuple, Sequence, cast

from sciencebeam_parser.document.layout_document import LayoutPageCoordinates
from sciencebeam_parser.document.semantic_document import (
    SemanticContentWrapper,
    SemanticGraphic
)


LOGGER = logging.getLogger(__name__)


class GraphicMatch(NamedTuple):
    semantic_graphic: SemanticGraphic
    candidate_semantic_content: SemanticContentWrapper


class GraphicMatchResult(NamedTuple):
    graphic_matches: Sequence[GraphicMatch]
    unmatched_graphics: Sequence[SemanticGraphic]

    def __len__(self):
        return len(self.graphic_matches)

    def __iter__(self):
        return iter(self.graphic_matches)


class GraphicMatcher(ABC):
    @abstractmethod
    def get_graphic_matches(
        self,
        semantic_graphic_list: Sequence[SemanticGraphic],
        candidate_semantic_content_list: Sequence[SemanticContentWrapper]
    ) -> GraphicMatchResult:
        pass


class BoundingBoxDistance(NamedTuple):
    page_number_diff: int
    delta_x: float = 0
    delta_y: float = 0
    euclidean_distance: float = 0

    def get_sort_key(self):
        return (self.page_number_diff, self.euclidean_distance,)


def get_bounding_box_distance(
    bounding_box_1: LayoutPageCoordinates,
    bounding_box_2: LayoutPageCoordinates
) -> BoundingBoxDistance:
    page_number_diff = abs(
        bounding_box_1.page_number - bounding_box_2.page_number
    )
    delta_x = max(
        0,
        bounding_box_2.x - (bounding_box_1.x + bounding_box_1.width),
        bounding_box_1.x - (bounding_box_2.x + bounding_box_2.width)
    )
    delta_y = max(
        0,
        bounding_box_2.y - (bounding_box_1.y + bounding_box_1.height),
        bounding_box_1.y - (bounding_box_2.y + bounding_box_2.height)
    )
    euclidean_distance = math.sqrt(delta_x**2 + delta_y**2)
    return BoundingBoxDistance(
        page_number_diff=page_number_diff,
        delta_x=delta_x,
        delta_y=delta_y,
        euclidean_distance=euclidean_distance
    )


def get_sorted_bounding_box_distances(
    bounding_box_distance_list: Iterable[BoundingBoxDistance]
) -> List[BoundingBoxDistance]:
    return sorted(
        bounding_box_distance_list,
        key=BoundingBoxDistance.get_sort_key
    )


def get_bounding_box_list_distance(
    bounding_box_list_1: Sequence[LayoutPageCoordinates],
    bounding_box_list_2: Sequence[LayoutPageCoordinates]
) -> BoundingBoxDistance:
    sorted_distances = get_sorted_bounding_box_distances([
        get_bounding_box_distance(bounding_box_1, bounding_box_2)
        for bounding_box_1 in bounding_box_list_1
        for bounding_box_2 in bounding_box_list_2
    ])
    return sorted_distances[0]


class BoundingBoxRef(NamedTuple):
    key: int
    bounding_box_list: Sequence[LayoutPageCoordinates]
    semantic_content: SemanticContentWrapper

    def get_distance_to(self, other: 'BoundingBoxRef') -> BoundingBoxDistance:
        return get_bounding_box_list_distance(
            self.bounding_box_list,
            other.bounding_box_list
        )


class BoundingBoxDistanceBetween(NamedTuple):
    bounding_box_distance: BoundingBoxDistance
    bounding_box_ref_1: BoundingBoxRef
    bounding_box_ref_2: BoundingBoxRef

    def get_sort_key(self):
        return self.bounding_box_distance.get_sort_key()


class BoundingBoxDistanceGraphicMatcher(GraphicMatcher):
    def __init__(self):
        super().__init__()
        # we ignore svgs for now because they currently represent the whole page
        # rather than individual images
        self.ignored_graphic_types = {'svg'}

    def is_accept_distance(self, distance_between: BoundingBoxDistanceBetween) -> bool:
        return distance_between.bounding_box_distance.page_number_diff == 0

    def get_graphic_matches(
        self,
        semantic_graphic_list: Sequence[SemanticGraphic],
        candidate_semantic_content_list: Sequence[SemanticContentWrapper]
    ) -> GraphicMatchResult:
        graphic_bounding_box_ref_list = [
            BoundingBoxRef(
                id(semantic_graphic),
                bounding_box_list=[semantic_graphic.layout_graphic.coordinates],
                semantic_content=semantic_graphic
            )
            for semantic_graphic in semantic_graphic_list
            if (
                semantic_graphic.layout_graphic
                and semantic_graphic.layout_graphic.coordinates
                and semantic_graphic.layout_graphic.graphic_type not in self.ignored_graphic_types
            )
        ]
        candidate_bounding_box_ref_list = [
            BoundingBoxRef(
                id(candidate_semantic_content),
                bounding_box_list=(
                    candidate_semantic_content
                    .merged_block
                    .get_merged_coordinates_list()
                ),
                semantic_content=candidate_semantic_content
            )
            for candidate_semantic_content in candidate_semantic_content_list
        ]
        best_distance_between_by_candidate_key: Dict[int, BoundingBoxDistanceBetween] = {}
        for graphic_bounding_box_ref in graphic_bounding_box_ref_list:
            sorted_distances_between = sorted(
                [
                    BoundingBoxDistanceBetween(
                        bounding_box_distance=graphic_bounding_box_ref.get_distance_to(
                            candidate_bounding_box_ref
                        ),
                        bounding_box_ref_1=graphic_bounding_box_ref,
                        bounding_box_ref_2=candidate_bounding_box_ref
                    )
                    for candidate_bounding_box_ref in candidate_bounding_box_ref_list
                ],
                key=BoundingBoxDistanceBetween.get_sort_key
            )
            if not sorted_distances_between:
                continue
            best_distance_between = sorted_distances_between[0]
            if not self.is_accept_distance(best_distance_between):
                LOGGER.debug('not accepting distance: %r', best_distance_between)
                continue
            candidate_key = best_distance_between.bounding_box_ref_2.key
            previous_best_distance_between = (
                best_distance_between_by_candidate_key.get(candidate_key)
            )
            if (
                previous_best_distance_between
                and (
                    previous_best_distance_between.get_sort_key()
                    < best_distance_between.get_sort_key()
                )
            ):
                LOGGER.debug(
                    'found better previous best distance between: %r > %r',
                    previous_best_distance_between,
                    best_distance_between
                )
                continue
            if previous_best_distance_between:
                LOGGER.debug(
                    'found better best distance between: %r < %r',
                    previous_best_distance_between,
                    best_distance_between
                )
            best_distance_between_by_candidate_key[
                candidate_key
            ] = best_distance_between
        graphic_matches = [
            GraphicMatch(
                semantic_graphic=cast(
                    SemanticGraphic,
                    distance_between.bounding_box_ref_1.semantic_content
                ),
                candidate_semantic_content=(
                    distance_between.bounding_box_ref_2.semantic_content
                )
            )
            for distance_between in best_distance_between_by_candidate_key.values()
        ]
        matched_graphic_keys = {
            distance_between.bounding_box_ref_1.key
            for distance_between in best_distance_between_by_candidate_key.values()
        }
        unmatched_graphics = [
            semantic_graphic
            for semantic_graphic in semantic_graphic_list
            if id(semantic_graphic) not in matched_graphic_keys
        ]
        return GraphicMatchResult(
            graphic_matches=graphic_matches,
            unmatched_graphics=unmatched_graphics
        )
