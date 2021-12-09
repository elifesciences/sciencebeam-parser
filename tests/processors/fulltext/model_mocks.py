import logging
from typing import Dict, Iterable, Mapping, Union
from unittest.mock import MagicMock

from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument
)
from sciencebeam_parser.models.data import (
    AppFeaturesContext,
    DocumentFeaturesContext
)
from sciencebeam_parser.models.model import NEW_DOCUMENT_MARKER, NewDocumentMarker
from sciencebeam_parser.models.model import LayoutModelLabel, Model
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
        model_wrapper._iter_label_layout_documents = (  # type: ignore
            self._iter_label_layout_documents
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

    def _iter_label_layout_documents(
        self,
        layout_documents: Iterable[LayoutDocument],
        app_features_context: AppFeaturesContext
    ) -> Iterable[Union[LayoutModelLabel, NewDocumentMarker]]:
        for index, layout_document in enumerate(layout_documents):
            if index > 0:
                yield NEW_DOCUMENT_MARKER
            yield from self._iter_label_layout_document(
                layout_document,
                app_features_context=app_features_context
            )

    def _iter_label_layout_document(
        self,
        layout_document: LayoutDocument,
        app_features_context: AppFeaturesContext
    ) -> Iterable[LayoutModelLabel]:
        data_generator = self._model_wrapper.get_data_generator(
            document_features_context=DocumentFeaturesContext(
                app_features_context=app_features_context
            )
        )
        LOGGER.debug('_label_by_layout_token.keys: %s', self._label_by_layout_token.keys())
        for model_data in data_generator.iter_model_data_for_layout_document(layout_document):
            if model_data.layout_token:
                label = self._label_by_layout_token.get(
                    id(model_data.layout_token),
                    self._default_label
                )
                LOGGER.debug('id(layout_token)=%r, label=%r', id(model_data.layout_token), label)
            else:
                assert model_data.layout_line
                first_layout_token = model_data.layout_line.tokens[0]
                label = self._label_by_layout_token.get(
                    id(first_layout_token),
                    self._default_label
                )
                LOGGER.debug('id(first_layout_token)=%r, label=%r', id(first_layout_token), label)
            yield LayoutModelLabel(
                label=label,
                label_token_text='dummy',
                layout_line=model_data.layout_line,
                layout_token=model_data.layout_token
            )


class MockFullTextModels(FullTextModels):
    def __init__(self):
        model_impl_mock = MagicMock('model_impl')
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
            citation_model=CitationModel(model_impl_mock)
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
