import logging
from typing import Optional, Iterable, NamedTuple, List, Tuple

import tensorflow as tf

from delft.sequenceLabelling.evaluation import (
    get_entities
)

from sciencebeam_trainer_delft.sequence_labelling.reader import load_data_crf_lines
from sciencebeam_trainer_delft.sequence_labelling.wrapper import Sequence

from pygrobid.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutToken,
    join_layout_tokens
)
from pygrobid.models.model import Model


LOGGER = logging.getLogger(__name__)


class LabeledLayoutToken(NamedTuple):
    label: str
    layout_token: LayoutToken


def iter_entity_values_predicted_labels(
    tag_result: List[Tuple[str, str]]
) -> Iterable[Tuple[str, str]]:
    tokens, labels = zip(*tag_result)
    LOGGER.debug('tokens: %s', tokens)
    LOGGER.debug('labels: %s', labels)
    for tag, start, end in get_entities(list(labels)):
        yield tag, ' '.join(tokens[start:end + 1])


def iter_entity_values_for_labeled_layout_tokens(
    labeled_layout_tokens: Iterable[LabeledLayoutToken]
) -> Iterable[Tuple[str, str]]:
    layout_tokens = [result.layout_token for result in labeled_layout_tokens]
    labels = [result.label for result in labeled_layout_tokens]
    LOGGER.debug('layout_tokens: %s', layout_tokens)
    LOGGER.debug('labels: %s', labels)
    for tag, start, end in get_entities(list(labels)):
        yield tag, join_layout_tokens(layout_tokens[start:end + 1])


def iter_entity_layout_blocks_for_labeled_layout_tokens(
    labeled_layout_tokens: Iterable[LabeledLayoutToken]
) -> Iterable[Tuple[str, LayoutBlock]]:
    layout_tokens = [result.layout_token for result in labeled_layout_tokens]
    labels = [result.label for result in labeled_layout_tokens]
    LOGGER.debug('layout_tokens: %s', layout_tokens)
    LOGGER.debug('labels: %s', labels)
    for tag, start, end in get_entities(list(labels)):
        yield tag, LayoutBlock.for_tokens(layout_tokens[start:end + 1])


class SeparateSessionSequenceWrapper(Sequence):
    def __init__(self, *args, **kwargs):
        self._graph = tf.Graph()
        self._session = tf.Session(graph=self._graph)
        super().__init__(*args, **kwargs)

    def load_from(self, *args, **kwargs):
        with self._graph.as_default():
            with self._session.as_default():
                return super().load_from(*args, **kwargs)

    def tag(self, *args, **kwargs):
        with self._graph.as_default():
            with self._session.as_default():
                return super().tag(*args, **kwargs)


class DelftModel(Model):
    def __init__(self, model_url: str):
        self.model_url = model_url
        self._model: Optional[Sequence] = None

    @property
    def model(self) -> Sequence:
        if self._model is not None:
            return self._model
        model = SeparateSessionSequenceWrapper('dummy-model')
        model.load_from(self.model_url)
        self._model = model
        return model

    def iter_predict_labels_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> Iterable[LabeledLayoutToken]:
        data_generator = self.get_data_generator()
        model_data_list = list(data_generator.iter_model_data_for_layout_document(layout_document))
        data_lines = [model_data.data_line for model_data in model_data_list]
        texts, features = load_data_crf_lines(data_lines)
        texts = texts.tolist()
        LOGGER.debug('texts: %s', texts)
        tag_result = self.predict_labels(
            texts=texts, features=features, output_format=None
        )
        LOGGER.debug('model_data_list: %s', model_data_list)
        LOGGER.debug('tag_result: %s', tag_result)
        for model_data, token_tag in zip(model_data_list, tag_result[0]):
            token, tag = token_tag
            assert model_data.layout_token
            assert token == model_data.layout_token.text, \
                f'actual: {repr(token)}, expected: {repr(model_data.layout_token.text)}'
            yield LabeledLayoutToken(label=tag, layout_token=model_data.layout_token)

    def predict_labels_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> List[LabeledLayoutToken]:
        return list(self.iter_predict_labels_for_layout_document(layout_document))

    def predict_labels(
        self,
        texts: List[List[str]],
        features: List[List[List[str]]],
        output_format: Optional[str] = None
    ) -> List[List[Tuple[str, str]]]:
        model = self.model
        return model.tag(texts, features=features, output_format=output_format)

    def iter_entity_values_predicted_labels(
        self,
        tag_result: List[Tuple[str, str]]
    ) -> Iterable[Tuple[str, str]]:
        return iter_entity_values_predicted_labels(tag_result)

    def iter_entity_values_for_labeled_layout_tokens(
        self,
        labeled_layout_tokens: Iterable[LabeledLayoutToken]
    ) -> Iterable[Tuple[str, str]]:
        return iter_entity_values_for_labeled_layout_tokens(labeled_layout_tokens)

    def iter_entity_layout_blocks_for_labeled_layout_tokens(
        self,
        labeled_layout_tokens: Iterable[LabeledLayoutToken]
    ) -> Iterable[Tuple[str, LayoutBlock]]:
        return iter_entity_layout_blocks_for_labeled_layout_tokens(labeled_layout_tokens)
