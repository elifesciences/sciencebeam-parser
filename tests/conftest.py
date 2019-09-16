import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from py._path.local import LocalPath

from tests.utils.mock_server import MockServer

from .compat_patch_mock import patch_magicmock_fixture  # noqa pylint: disable=unused-import


@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    logging.root.handlers = []
    logging.basicConfig(level='WARNING')
    logging.getLogger('sciencebeam').setLevel('DEBUG')
    logging.getLogger('tests').setLevel('DEBUG')


@pytest.fixture
def temp_dir(tmpdir: LocalPath):
    # convert to standard Path
    return Path(str(tmpdir))


@pytest.fixture
def mock_server():
    server = MockServer()
    try:
        server.start()
        yield server
    finally:
        server.stop()


@pytest.fixture(name='requests_session_class_mock')
def _requests_session_class():
    with patch('requests.Session') as mock:
        yield mock


@pytest.fixture(name='requests_session_mock')
def _requests_session(requests_session_class_mock: MagicMock):
    return requests_session_class_mock.return_value.__enter__.return_value


@pytest.fixture(name='requests_session_post_mock')
def _requests_session_post(requests_session_mock: MagicMock):
    return requests_session_mock.post
