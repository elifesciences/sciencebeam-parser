from unittest.mock import MagicMock

import pytest

from sciencebeam_parser.utils.background_process import BackgroundProcess


@pytest.fixture(name='process_mock')
def _process_mock():
    return MagicMock(name='process')


class TestBackgroundProcess:
    def test_should_implement_repr(self, process_mock: MagicMock):
        process_mock.pid = 123
        process_mock.returncode = 42
        assert repr(BackgroundProcess(process_mock)) == (
            'BackgroundProcess(pid=123, returncode=42)'
        )
