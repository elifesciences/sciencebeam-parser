from pathlib import Path
import fsspec

from sciencebeam_parser.utils.io import (
    get_file_system_for_url,
    get_fully_qualified_path_for_fs_and_path,
    get_fully_qualified_path_for_protocol_and_path,
    glob
)


class TestGetFileSystemForUrl:
    def test_should_return_gs_file_system_for_gs_protocol(self):
        fs = get_file_system_for_url('gs://path')
        assert 'gs' in fs.protocol

    def test_should_return_local_file_system_for_file_protocol(self):
        fs = get_file_system_for_url('file://path')
        assert 'file' in fs.protocol

    def test_should_return_local_file_system_for_path_without_protocol(self):
        fs = get_file_system_for_url('/path')
        assert 'file' in fs.protocol


class TestGetFullUrlForProtocolAndPath:
    def test_should_keep_local_absolute_path_unchanged(self):
        assert get_fully_qualified_path_for_protocol_and_path(
            'file', '/path/to/file'
        ) == '/path/to/file'

    def test_should_add_protocol_to_relative_remote_path(self):
        assert get_fully_qualified_path_for_protocol_and_path(
            'gs', 'path/to/file'
        ) == 'gs://path/to/file'


class TestGetFullUrlForFsAndPath:
    def test_should_keep_local_absolute_path_unchanged(self):
        fs = fsspec.filesystem('file')
        assert get_fully_qualified_path_for_fs_and_path(
            fs, '/path/to/file'
        ) == '/path/to/file'

    def test_should_add_protocol_to_relative_remote_path(self):
        fs = fsspec.filesystem('gs')
        assert get_fully_qualified_path_for_fs_and_path(
            fs, 'path/to/file'
        ) == 'gcs://path/to/file'


class TestGlob:
    def test_should_find_local_files(self, tmp_path: Path):
        file1 = (tmp_path / 'test1.file')
        file1.touch()
        assert list(glob(str(tmp_path) + '/test*.file')) == [str(file1)]
