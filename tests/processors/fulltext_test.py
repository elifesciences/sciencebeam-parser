import logging
from typing import Dict, Iterable, List, Mapping
from unittest.mock import MagicMock

import pytest

from pygrobid.document.layout_document import LayoutBlock, LayoutDocument, LayoutPage
from pygrobid.models.delft_model import DelftModel, LabeledLayoutToken
from pygrobid.models.model import LayoutModelLabel
from pygrobid.models.segmentation.model import SegmentationModel
from pygrobid.models.header.model import HeaderModel
from pygrobid.models.fulltext.model import FullTextModel
from pygrobid.processors.fulltext import (
    FullTextProcessor,
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
    def __init__(self, model_impl: DelftModel):
        self._model_impl = model_impl
        self._label_by_layout_token: Dict[LayoutTokenId, str] = {}
        self._default_label = 'O'
        model_impl._model = MagicMock(name='delft_model')
        model_impl.iter_label_layout_document = (  # type: ignore
            self._iter_label_layout_document
        )
        model_impl.iter_predict_labels_for_layout_document = (  # type: ignore
            self._iter_predict_labels_for_layout_document
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

    def _iter_label_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> Iterable[LayoutModelLabel]:
        data_generator = self._model_impl.get_data_generator()
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

    def _iter_predict_labels_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> Iterable[LabeledLayoutToken]:
        LOGGER.debug('iter_predict_labels_for_layout_document: %s', layout_document)
        data_generator = self._model_impl.get_data_generator()
        LOGGER.debug('_label_by_layout_token.keys: %s', self._label_by_layout_token.keys())
        for model_data in data_generator.iter_model_data_for_layout_document(layout_document):
            assert model_data.layout_token
            label = self._label_by_layout_token.get(
                id(model_data.layout_token),
                self._default_label
            )
            LOGGER.debug('id(layout_token)=%r, label=%r', id(model_data.layout_token), label)
            yield LabeledLayoutToken(
                label=label,
                layout_token=model_data.layout_token
            )


class MockFullTextModels(FullTextModels):
    def __init__(self):
        super().__init__(
            segmentation_model=SegmentationModel('dummy-segmentation-model'),
            header_model=HeaderModel('dummy-header-model'),
            fulltext_model=FullTextModel('dummy-fulltext-model')
        )
        self.segmentation_model_mock = MockDelftModelWrapper(self.segmentation_model)
        self.header_model_mock = MockDelftModelWrapper(self.header_model)
        self.fulltext_model_mock = MockDelftModelWrapper(self.fulltext_model)


@pytest.fixture(name='fulltext_models_mock')
def _fulltext_models() -> MockFullTextModels:
    return MockFullTextModels()


def _get_layout_model_labels_for_block(
    layout_block: LayoutBlock,
    label: str
) -> List[LayoutModelLabel]:
    return [
        LayoutModelLabel(
            label=label,
            label_token_text=layout_token.text,
            layout_line=layout_line,
            layout_token=layout_token
        )
        for layout_line in layout_block.lines
        for layout_token in layout_line.tokens
    ]


class TestFullTextProcessor:
    def test_should_not_fail_with_empty_document(
        self, fulltext_models_mock: MockFullTextModels
    ):
        fulltext_processor = FullTextProcessor(fulltext_models_mock)
        layout_document = LayoutDocument(pages=[])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        assert semantic_document is not None

    def test_should_extract_from_document(
        self, fulltext_models_mock: MockFullTextModels
    ):
        fulltext_processor = FullTextProcessor(fulltext_models_mock)
        header_block = LayoutBlock.for_text('This is the header')
        body_block = LayoutBlock.for_text('This is the body')
        back_block = LayoutBlock.for_text('This is the back')

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        header_model_mock = fulltext_models_mock.header_model_mock
        fulltext_model_mock = fulltext_models_mock.fulltext_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            header_block, '<header>'
        )
        segmentation_model_mock.update_label_by_layout_block(
            body_block, '<body>'
        )
        segmentation_model_mock.update_label_by_layout_block(
            back_block, '<annex>'
        )

        header_model_mock.update_label_by_layout_block(
            header_block, '<title>'
        )

        fulltext_model_mock.update_label_by_layout_block(
            body_block, '<paragraph>'
        )
        fulltext_model_mock.update_label_by_layout_block(
            back_block, '<paragraph>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            header_block,
            body_block,
            back_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        assert semantic_document is not None
        assert semantic_document.meta.title.get_text() == header_block.text
        assert semantic_document.body_section.get_text() == body_block.text
        assert semantic_document.back_section.get_text() == back_block.text
