from dataclasses import dataclass
from typing import Optional

from sciencebeam_trainer_delft.utils.download_manager import DownloadManager


DEFAULT_WAPITI_PATH = 'wapiti'


def install_wapiti_and_get_path_or_none(
    install_url: Optional[str],
    download_manager: DownloadManager
) -> Optional[str]:
    from sciencebeam_trainer_delft.sequence_labelling.engines.wapiti_install import (  # noqa pylint: disable=import-outside-toplevel
        install_wapiti_and_get_path_or_none as _install_wapiti_and_get_path_or_none
    )
    return _install_wapiti_and_get_path_or_none(
        install_url,
        download_manager=download_manager
    )


@dataclass
class LazyWapitiBinaryWrapper:
    download_manager: DownloadManager
    install_url: Optional[str] = None
    _binary_path: Optional[str] = None

    def get_binary_path(self) -> str:
        if not self.install_url:
            return DEFAULT_WAPITI_PATH
        if self._binary_path:
            return self._binary_path
        self._binary_path = install_wapiti_and_get_path_or_none(
            self.install_url,
            download_manager=self.download_manager
        ) or DEFAULT_WAPITI_PATH
        return self._binary_path
