import logging

import pytest


@pytest.fixture(autouse=True)
def configure_logging():
    logging.root.setLevel('INFO')
    for name in ['tests', 'pygrobid']:
        logging.getLogger(name).setLevel('DEBUG')
