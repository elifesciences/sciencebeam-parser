import os
import codecs
from contextlib import contextmanager
from typing import Iterable, Sequence
from urllib.parse import urlparse

import fsspec

from sciencebeam_trainer_delft.utils.io import (
    auto_uploading_output_file as _auto_uploading_output_file,
    is_external_location,
    open_file
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


@contextmanager
def auto_uploading_binary_output_file(filepath: str, **kwargs):
    if not is_external_location(filepath):
        # Note: the upstream implementation doesn't currently auto-compress local files
        file_dirname = os.path.dirname(filepath)
        if file_dirname:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open_file(filepath, mode='wb', **kwargs) as fp:
            yield fp
            return
    with _auto_uploading_output_file(filepath, 'wb', **kwargs) as fp:
        yield fp


@contextmanager
def auto_uploading_text_output_file(filepath: str, encoding: str, **kwargs):
    with auto_uploading_binary_output_file(filepath, **kwargs) as fp:
        yield codecs.getwriter(encoding)(fp)


def auto_uploading_output_file(filepath: str, mode: str, encoding: str = 'utf-8', **kwargs):
    if mode == 'w':
        return auto_uploading_text_output_file(filepath, encoding=encoding, **kwargs)
    if mode == 'wb':
        return auto_uploading_binary_output_file(filepath, **kwargs)
    raise ValueError('invalid mode: %r' % mode)


def write_bytes(filepath: str, data: bytes, **kwargs):
    with auto_uploading_output_file(filepath, mode='wb', **kwargs) as fp:
        fp.write(data)


def write_text(filepath: str, text: str, encoding: str, **kwargs):
    # Note: the upstream implementation doesn't support encoding with compression
    write_bytes(
        filepath,
        codecs.encode(text, encoding=encoding),
        **kwargs
    )
