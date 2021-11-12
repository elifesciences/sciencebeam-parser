import logging
from typing import Optional, List, Tuple

import tensorflow as tf

from sciencebeam_trainer_delft.embedding.manager import EmbeddingManager
from sciencebeam_trainer_delft.sequence_labelling.wrapper import (
    DEFAULT_EMBEDDINGS_PATH,
    Sequence
)

from sciencebeam_parser.app.context import AppContext
from sciencebeam_parser.models.model_impl import ModelImpl
from sciencebeam_parser.utils.lazy import LazyLoaded


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


class DelftModelImpl(ModelImpl):
    def __init__(self, model_url: str, app_context: AppContext):
        self.model_url = model_url
        self.app_context = app_context
        self._lazy_model = LazyLoaded[Sequence](self._load_model)

    def __repr__(self) -> str:
        return '%s(%r, loaded=%r)' % (
            type(self).__name__, self.model_url, self._lazy_model.is_loaded
        )

    def _load_model(self) -> Sequence:
        embedding_registry_path = DEFAULT_EMBEDDINGS_PATH
        embedding_manager = EmbeddingManager(
            path=embedding_registry_path,
            download_manager=self.app_context.download_manager
        )
        model = SeparateSessionSequenceWrapper(
            'dummy-model',
            embedding_manager=embedding_manager
        )
        model.load_from(self.model_url)
        LOGGER.info('loaded delft model: %r', self.model_url)
        return model

    @property
    def model(self) -> Sequence:
        return self._lazy_model.get()

    def preload(self):
        self._lazy_model.get()

    def predict_labels(
        self,
        texts: List[List[str]],
        features: List[List[List[str]]],
        output_format: Optional[str] = None
    ) -> List[List[Tuple[str, str]]]:
        model = self.model
        return model.tag(texts, features=features, output_format=output_format)
