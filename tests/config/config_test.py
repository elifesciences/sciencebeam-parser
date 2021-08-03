from pathlib import Path
from typing import Iterable
from unittest.mock import patch

import pytest
import yaml

from sciencebeam_parser.config.config import AppConfig


@pytest.fixture(name='env_vars_mock')
def _env_vars_mock() -> Iterable[dict]:
    mock: dict
    with patch('os.environ', {}) as mock:
        yield mock


class TestAppConfig:
    def test_should_load_yaml(self, tmp_path: Path):
        config_path = tmp_path / 'config.yml'
        config_path.write_text(yaml.dump({
            'key1': 'value1'
        }))
        config = AppConfig.load_yaml(str(config_path))
        assert config.props['key1'] == 'value1'

    def test_should_override_top_level_value_with_env_var(
        self,
        tmp_path: Path,
        env_vars_mock: dict
    ):
        env_vars_mock['SCIENCEBEAM_PARSER__KEY1'] = 'updated value1'
        config_path = tmp_path / 'config.yml'
        config_path.write_text(yaml.dump({
            'key1': 'value1'
        }))
        config = AppConfig.load_yaml(str(config_path))
        config = config.apply_environment_variables()
        assert config.props['key1'] == 'updated value1'

    def test_should_override_nested_value_with_env_var(
        self,
        tmp_path: Path,
        env_vars_mock: dict
    ):
        env_vars_mock['SCIENCEBEAM_PARSER__PARENT1__KEY1'] = 'updated value1'
        config_path = tmp_path / 'config.yml'
        config_path.write_text(yaml.dump({
            'parent1': {
                'key1': 'original value1'
            }
        }))
        original_config = AppConfig.load_yaml(str(config_path))
        config = original_config.apply_environment_variables()
        assert config.props['parent1']['key1'] == 'updated value1'
        assert original_config.props['parent1']['key1'] == 'original value1'

    def test_should_override_int_value_with_env_var(
        self,
        tmp_path: Path,
        env_vars_mock: dict
    ):
        env_vars_mock['SCIENCEBEAM_PARSER__KEY1'] = '222'
        config_path = tmp_path / 'config.yml'
        config_path.write_text(yaml.dump({
            'key1': 111
        }))
        config = AppConfig.load_yaml(str(config_path))
        config = config.apply_environment_variables()
        assert config.props['key1'] == 222
