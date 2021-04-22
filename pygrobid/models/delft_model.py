import logging
from typing import Optional, Iterable, List, Tuple

import tensorflow as tf

from delft.sequenceLabelling.evaluation import (
    get_entities
)

from sciencebeam_trainer_delft.sequence_labelling.wrapper import Sequence

from pygrobid.models.model import Model


LOGGER = logging.getLogger(__name__)


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

    def predict_labels(
        self,
        texts: List[List[str]],
        features: List[List[List[str]]],
        output_format: Optional[str] = None
    ) -> Iterable[str]:
        model = self.model
        return model.tag(texts, features=features, output_format=output_format)

    def iter_entity_values_predicted_labels(
        self,
        tag_result: List[Tuple[str, str]]
    ) -> Iterable[Tuple[str, str]]:
        tokens, labels = zip(*tag_result)
        LOGGER.info('tokens: %s', tokens)
        LOGGER.info('labels: %s', labels)
        for tag, start, end in get_entities(list(labels)):
            yield tag, ' '.join(tokens[start:end])
