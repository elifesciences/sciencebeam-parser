from unittest.mock import MagicMock

import pytest


def _backport_assert_called(mock: MagicMock):
    assert mock.called


@pytest.fixture(scope='session', autouse=True)
def patch_magicmock_fixture():
    try:
        MagicMock.assert_called
    except AttributeError:
        MagicMock.assert_called = _backport_assert_called
