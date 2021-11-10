import logging
from pathlib import Path

import pytest
import yaml

from sciencebeam_parser.resources.default_config import DEFAULT_CONFIG_FILE


@pytest.fixture(autouse=True)
def configure_logging():
    logging.root.setLevel('INFO')
    for name in ['tests', 'sciencebeam_parser']:
        logging.getLogger(name).setLevel('DEBUG')


@pytest.fixture(scope='session')
def sciencebeam_parser_config() -> dict:
    return yaml.safe_load(
        Path(DEFAULT_CONFIG_FILE).read_text(encoding='utf-8')
    )
