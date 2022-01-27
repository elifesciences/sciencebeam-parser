from unittest.mock import MagicMock

import pytest

from tests.processors.fulltext.model_mocks import MockFullTextModels


@pytest.fixture(name='fulltext_models_mock')
def _fulltext_models_mock() -> MockFullTextModels:
    return MockFullTextModels()


@pytest.fixture(name='sciencebeam_parser_mock')
def _sciencebeam_parser_mock(
    fulltext_models_mock: MockFullTextModels
) -> MagicMock:
    mock = MagicMock(name='ScienceBeamParser')
    mock.fulltext_models = fulltext_models_mock
    return mock


@pytest.fixture(name='sciencebeam_parser_class_mock')
def _sciencebeam_parser_class_mock(
    sciencebeam_parser_mock: MagicMock
) -> MagicMock:
    mock = MagicMock(name='ScienceBeamParser_class')
    mock.from_config.return_value = sciencebeam_parser_mock
    return mock
