import logging
from pathlib import Path

import pytest
import yaml


@pytest.fixture(autouse=True)
def configure_logging():
    logging.root.setLevel('INFO')
    for name in ['tests', 'pygrobid']:
        logging.getLogger(name).setLevel('DEBUG')


@pytest.fixture(scope='session')
def pygrobid_config() -> dict:
    return yaml.safe_load(Path('config.yml').read_text())
