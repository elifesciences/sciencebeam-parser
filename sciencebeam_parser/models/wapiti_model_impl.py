import os
import logging
import threading
from typing import Iterable, Optional, List, Tuple

import numpy as np

from sciencebeam_trainer_delft.sequence_labelling.engines.wapiti import WapitiWrapper
from sciencebeam_trainer_delft.utils.io import copy_file
from sciencebeam_trainer_delft.utils.download_manager import DownloadManager
from sciencebeam_trainer_delft.sequence_labelling.engines.wapiti_adapters import (
    WapitiModelAdapter,
    WapitiModel
)

from sciencebeam_parser.app.context import AppContext
from sciencebeam_parser.models.model_impl import ModelImpl


LOGGER = logging.getLogger(__name__)


class WapitiServiceModelAdapter(WapitiModelAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.Lock()

    @staticmethod
    def load_from(
            model_path: str,
            download_manager: DownloadManager,
            wapiti_binary_path: str = None) -> 'WapitiModelAdapter':
        # overriding method to return WapitiServiceModelAdapter
        model_file_path = os.path.join(model_path, 'model.wapiti.gz')
        local_model_file_path = None
        try:
            local_model_file_path = download_manager.download_if_url(model_file_path)
        except FileNotFoundError:
            pass
        if not local_model_file_path or not os.path.isfile(str(local_model_file_path)):
            model_file_path = os.path.splitext(model_file_path)[0]
            local_model_file_path = download_manager.download_if_url(model_file_path)
        LOGGER.debug('local_model_file_path: %s', local_model_file_path)
        if local_model_file_path.endswith('.gz'):
            local_uncompressed_file_path = os.path.splitext(local_model_file_path)[0]
            copy_file(local_model_file_path, local_uncompressed_file_path, overwrite=False)
            local_model_file_path = local_uncompressed_file_path
        return WapitiServiceModelAdapter(
            WapitiWrapper(
                wapiti_binary_path=wapiti_binary_path
            ),
            model_file_path=local_model_file_path,
            model_path=model_path
        )

    def iter_tag(
        self,
        x: np.ndarray,
        features: np.ndarray,
        output_format: str = None
    ) -> Iterable[List[Tuple[str, str]]]:
        # by default, WapitiModelAdapter will run the binary for each call
        # using "iter_tag_using_model" will result in a wapiti process
        # that we communicate with via stdin / stdout
        with self._lock:
            return self.iter_tag_using_model(x, features, output_format)


class WapitiModelImpl(ModelImpl):
    def __init__(self, model_url: str, app_context: AppContext):
        self.model_url = model_url
        self.app_context = app_context
        self._model: Optional[WapitiModelAdapter] = None

    def __repr__(self) -> str:
        return '%s(%r, loaded=%r)' % (
            type(self).__name__, self.model_url, self._model is not None
        )

    @property
    def model(self) -> WapitiModel:
        if self._model is not None:
            return self._model
        model = WapitiServiceModelAdapter.load_from(
            self.model_url,
            wapiti_binary_path=self.app_context.lazy_wapiti_binary_wrapper.get_binary_path(),
            download_manager=self.app_context.download_manager
        )
        self._model = model
        return model

    def predict_labels(
        self,
        texts: List[List[str]],
        features: List[List[List[str]]],
        output_format: Optional[str] = None
    ) -> List[List[Tuple[str, str]]]:
        model = self.model
        result = model.tag(texts, features=features, output_format=output_format)
        token_count = sum(len(text) for text in texts)
        LOGGER.info(
            'predicted labels using wapiti model (document count: %d, token count: %d)',
            len(texts), token_count
        )
        return result
