import logging
import os
import copy
from pathlib import Path
from typing import Any, Optional, Union

import yaml


LOGGER = logging.getLogger(__name__)


DEFAULT_DOWNLOAD_DIR = 'data/download'


def parse_env_value(value: str) -> Union[str, int]:
    return yaml.safe_load(value)


class AppConfig:
    def __init__(self, props: dict):
        self.props = props

    def __repr__(self) -> str:
        return '%s(%r)' % (type(self).__name__, self.props)

    @staticmethod
    def load_yaml(file_path: str) -> 'AppConfig':
        return AppConfig(
            yaml.safe_load(Path(file_path).read_text(encoding='utf-8'))
        )

    def apply_environment_variables(self, prefix: str = 'SCIENCEBEAM_PARSER__') -> 'AppConfig':
        updated_props = copy.deepcopy(self.props)
        env_vars = os.environ
        if not env_vars:
            LOGGER.debug('no environment variables')
        LOGGER.debug('processing env vars: %r', env_vars)
        for env_name, env_value in env_vars.items():
            if not env_name.startswith(prefix):
                LOGGER.debug('ignoring: %r', env_name)
                continue
            key_path = env_name[len(prefix):].lower().split('__')
            LOGGER.debug('updating: %r -> %r', env_name, key_path)
            parent_key_path = key_path[:-1]
            leaf_key = key_path[-1]
            parent_props = updated_props
            for parent_key in parent_key_path:
                parent_props = parent_props.setdefault(parent_key, {})
            parent_props[leaf_key] = parse_env_value(env_value)
        return AppConfig(updated_props)

    def get(self, key: str, default_value: Optional[Any] = None):
        return self.props.get(key, default_value)

    def __getitem__(self, key: str):
        return self.props[key]


def get_download_dir(config: Union[dict, AppConfig]) -> str:
    return os.path.expanduser(
        config.get('download_dir', DEFAULT_DOWNLOAD_DIR)
    )
