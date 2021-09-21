import os
import logging
from typing import Sequence

from sciencebeam_trainer_delft.utils.download_manager import DownloadManager
from sciencebeam_trainer_delft.utils.io import is_external_location


LOGGER = logging.getLogger(__name__)


def download_if_url_from_alternatives(
    download_manager: DownloadManager,
    alternative_file_url_or_path_list: Sequence[str]
) -> str:
    for file_url_or_path in alternative_file_url_or_path_list:
        if not is_external_location(file_url_or_path):
            if os.path.exists(file_url_or_path):
                return file_url_or_path
            LOGGER.debug('local file doesnt exist: %r', file_url_or_path)
            continue
        local_file = download_manager.get_local_file(file_url_or_path)
        if os.path.exists(local_file):
            return local_file
    LOGGER.debug(
        'no existing local files found, downloading: %r', alternative_file_url_or_path_list
    )
    for file_url_or_path in alternative_file_url_or_path_list:
        try:
            local_file = download_manager.download_if_url(file_url_or_path)
            if os.path.exists(local_file):
                return local_file
            LOGGER.debug(
                'local file for %r not found: %r',
                file_url_or_path, local_file
            )
        except FileNotFoundError:
            LOGGER.debug('remote file not found: %r', file_url_or_path)
    raise FileNotFoundError('no file found for %r' % alternative_file_url_or_path_list)
