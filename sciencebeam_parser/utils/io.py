from typing import Iterable, Sequence
from urllib.parse import urlparse

import fsspec

from sciencebeam_trainer_delft.utils.io import (
    auto_uploading_output_file
)


def get_file_system_protocol_for_url(url: str) -> fsspec.AbstractFileSystem:
    parsed_url = urlparse(url)
    return parsed_url.scheme or 'file'


def get_file_system_for_url(url: str) -> fsspec.AbstractFileSystem:
    return fsspec.filesystem(get_file_system_protocol_for_url(url))


def get_file_system_protocols(
    fs: fsspec.AbstractFileSystem
) -> Sequence[str]:
    return (fs.protocol,) if isinstance(fs.protocol, str) else fs.protocol


def get_file_system_default_protocol(
    fs: fsspec.AbstractFileSystem
) -> str:
    return get_file_system_protocols(fs)[0]


def get_fully_qualified_path_for_protocol_and_path(
    protocol: str,
    path: str
) -> str:
    if 'file' in protocol:
        return path
    return f'{protocol}://{path}'


def iter_fully_qualified_paths_for_protocol_and_paths(
    protocol: str,
    paths: Iterable[str]
) -> Iterable[str]:
    return (
        get_fully_qualified_path_for_protocol_and_path(protocol, path)
        for path in paths
    )


def get_fully_qualified_path_for_fs_and_path(
    fs: fsspec.AbstractFileSystem,
    path: str
) -> str:
    return get_fully_qualified_path_for_protocol_and_path(
        get_file_system_default_protocol(fs),
        path
    )


def glob(
    glob_pattern: str
) -> Sequence[str]:
    protocol = get_file_system_protocol_for_url(glob_pattern)
    fs: fsspec.AbstractFileSystem = fsspec.filesystem(protocol)
    return list(iter_fully_qualified_paths_for_protocol_and_paths(
        protocol,
        fs.glob(glob_pattern)
    ))


def makedirs(
    path: str,
    exist_ok: bool = False
):
    get_file_system_for_url(path).makedirs(path, exist_ok=exist_ok)


def write_bytes(filepath: str, data: bytes, **kwargs):
    with auto_uploading_output_file(filepath, mode='wb', **kwargs) as fp:
        fp.write(data)
