from typing import NamedTuple

from typing_extensions import Protocol

from sciencebeam_parser.config.config import AppConfig
from sciencebeam_parser.external.wapiti.wrapper import LazyWapitiBinaryWrapper


# using protocol to avoid delft import where we just need the typing hint
class DownloadManagerProtocol(Protocol):
    def get_local_file(self, file_url: str, auto_uncompress: bool = True) -> str:
        pass

    def is_downloaded(self, file_url: str, auto_uncompress: bool = True) -> bool:
        pass

    def download(
        self, file_url: str,
        local_file: str = None,
        auto_uncompress: bool = True,
        skip_if_downloaded: bool = True
    ) -> str:
        pass

    def download_if_url(self, file_url_or_path: str, **kwargs) -> str:
        pass


class AppContext(NamedTuple):
    app_config: AppConfig
    download_manager: DownloadManagerProtocol
    lazy_wapiti_binary_wrapper: LazyWapitiBinaryWrapper
