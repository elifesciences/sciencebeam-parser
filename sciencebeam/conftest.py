import logging

import pytest

@pytest.fixture(scope='session', autouse=True)
def setup_logging():
  logging.root.handlers = []
  logging.basicConfig(level='DEBUG')
