import logging
from pathlib import Path

import pytest
from py._path.local import LocalPath

from tests.utils.mock_server import MockServer


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
