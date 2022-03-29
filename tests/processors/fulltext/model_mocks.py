import logging
from typing import Callable, Dict, Iterable, Mapping, Sequence, TypeVar, Union
from unittest.mock import MagicMock

from sciencebeam_parser.document.layout_document import (
    LayoutBlock
)
from sciencebeam_parser.models.data import (
    LayoutModelData
)
from sciencebeam_parser.models.model import NEW_DOCUMENT_MARKER, NewDocumentMarker
from sciencebeam_parser.models.model import Model
from sciencebeam_parser.models.segmentation.model import SegmentationModel
from sciencebeam_parser.models.header.model import HeaderModel
from sciencebeam_parser.models.affiliation_address.model import AffiliationAddressModel
from sciencebeam_parser.models.name.model import NameModel
from sciencebeam_parser.models.fulltext.model import FullTextModel
from sciencebeam_parser.models.figure.model import FigureModel
from sciencebeam_parser.models.table.model import TableModel
from sciencebeam_parser.models.reference_segmenter.model import ReferenceSegmenterModel
from sciencebeam_parser.models.citation.model import CitationModel
from sciencebeam_parser.processors.fulltext.models import (
    FullTextModels
)


LOGGER = logging.getLogger(__name__)


T = TypeVar('T')


LayoutTokenId = int


def get_label_by_layout_token_for_block(
    layout_block: LayoutBlock,
    label: str
) -> Dict[LayoutTokenId, str]:
    return {
        id(layout_token): 'B-' + label if index == 0 else 'I-' + label
        for index, layout_token in enumerate(layout_block.iter_all_tokens())
    }


class MockDelftModelWrapper:
    def __init__(self, model_wrapper: Model):
        self._model_wrapper = model_wrapper
        self._label_by_layout_token: Dict[LayoutTokenId, str] = {}
        self._default_label = 'O'
        model_wrapper._lazy_model_impl._value = MagicMock(name='model_impl')
        model_wrapper._iter_flat_label_model_data_lists_to = (  # type: ignore
            self._iter_flat_label_model_data_lists_to
        )

    def update_label_by_layout_tokens(
        self,
        label_by_layout_token: Mapping[LayoutTokenId, str]
    ):
        self._label_by_layout_token.update(label_by_layout_token)

    def update_label_by_layout_block(
        self,
        layout_block: LayoutBlock,
        label: str
    ):
        self.update_label_by_layout_tokens(
            get_label_by_layout_token_for_block(layout_block, label)
        )

    def _iter_flat_label_model_data_lists_to(  # pylint: disable=too-many-locals
        self,
        model_data_list_iterable: Iterable[Sequence[LayoutModelData]],
        item_factory: Callable[[str, LayoutModelData], T]
    ) -> Iterable[Union[T, NewDocumentMarker]]:
        for index, model_data_list in enumerate(model_data_list_iterable):
            if index > 0:
                yield NEW_DOCUMENT_MARKER
            for model_data in model_data_list:
                if model_data.layout_token:
                    label = self._label_by_layout_token.get(
                        id(model_data.layout_token),
                        self._default_label
                    )
                    LOGGER.debug(
                        'id(layout_token)=%r, label=%r', id(model_data.layout_token), label
                    )
                else:
                    assert model_data.layout_line
                    first_layout_token = model_data.layout_line.tokens[0]
                    label = self._label_by_layout_token.get(
                        id(first_layout_token),
                        self._default_label
                    )
                    LOGGER.debug(
                        'id(first_layout_token)=%r, label=%r', id(first_layout_token), label
                    )
                yield item_factory(
                    label,
                    model_data
                )


class MockFullTextModels(FullTextModels):
    def __init__(self):
        model_impl_mock = MagicMock('model_impl')
        self.cv_model_mock = MagicMock(name='cv_model')
        super().__init__(
            segmentation_model=SegmentationModel(model_impl_mock),
            header_model=HeaderModel(model_impl_mock),
            name_header_model=NameModel(model_impl_mock),
            name_citation_model=NameModel(model_impl_mock),
            affiliation_address_model=AffiliationAddressModel(model_impl_mock),
            fulltext_model=FullTextModel(model_impl_mock),
            figure_model=FigureModel(model_impl_mock),
            table_model=TableModel(model_impl_mock),
            reference_segmenter_model=ReferenceSegmenterModel(model_impl_mock),
            citation_model=CitationModel(model_impl_mock),
            cv_model=self.cv_model_mock
        )
        self.segmentation_model_mock = MockDelftModelWrapper(self.segmentation_model)
        self.header_model_mock = MockDelftModelWrapper(self.header_model)
        self.name_header_model_mock = MockDelftModelWrapper(self.name_header_model)
        self.name_citation_model_mock = MockDelftModelWrapper(self.name_citation_model)
        self.affiliation_address_model_mock = MockDelftModelWrapper(
            self.affiliation_address_model
        )
        self.fulltext_model_mock = MockDelftModelWrapper(self.fulltext_model)
        self.figure_model_mock = MockDelftModelWrapper(self.figure_model)
        self.table_model_mock = MockDelftModelWrapper(self.table_model)
        self.reference_segmenter_model_mock = MockDelftModelWrapper(self.reference_segmenter_model)
        self.citation_model_mock = MockDelftModelWrapper(self.citation_model)
