from unittest.mock import MagicMock

import pytest

from sciencebeam_parser.transformers.doc_converter_wrapper import ListenerProcess


@pytest.fixture(name='process_mock')
def _process_mock():
    return MagicMock(name='process')


class TestListenerProcess:
    def test_should_implement_repr(self, process_mock: MagicMock):
        process_mock.__repr__ = lambda _: 'process1'  # type: ignore
        listener_process = ListenerProcess(
            port=1234,
            host='host1',
            connect_timeout=42
        )
        listener_process.command = ['the-program', 'arg1', 'arg2']
        listener_process.process = process_mock
        assert repr(listener_process) == (
            'ListenerProcess('
            'port=1234'
            ', host=host1'
            ', connect_timeout=42'
            ', command=' + repr(listener_process.command) +
            ', process=process1'
            ')'
        )
