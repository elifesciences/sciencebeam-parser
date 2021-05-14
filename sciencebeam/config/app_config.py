import configparser
import logging
import os


LOGGER = logging.getLogger(__name__)


def get_app_root():
    return os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '../..'
    ))


def get_app_config_filename():
    return os.path.join(get_app_root(), 'app.cfg')


def get_app_defaults_config_filename():
    return os.path.join(get_app_root(), 'app-defaults.cfg')


def parse_environment_variable_overrides(
        env_vars: dict, prefix='SCIENCEBEAM__', section_separator='__'):
    result = {}
    LOGGER.debug('env_vars: %r', env_vars)
    for key, value in env_vars.items():
        if not key.startswith(prefix):
            continue
        key_fragments = key[len(prefix):].split(section_separator)
        if len(key_fragments) != 2:
            LOGGER.debug('key fragments not 2: %s', key_fragments)
            continue
        section_name, option_name = key_fragments
        result.setdefault(section_name.lower(), {})[option_name.lower()] = value
    LOGGER.debug('env var overrides: %s', result)
    return result


def get_environment_variable_overrides(**kwargs):
    return parse_environment_variable_overrides(os.environ, **kwargs)


def apply_environment_variable_overrides(
        config: configparser.ConfigParser,
        env_var_overrides: dict):
    for section_name, section_options in env_var_overrides.items():
        for option_name, value in section_options.items():
            config.set(section_name, option_name, value)


def read_app_config():
    config = configparser.ConfigParser()
    config.read([
        get_app_defaults_config_filename(),
        get_app_config_filename()
    ])
    apply_environment_variable_overrides(
        config,
        get_environment_variable_overrides()
    )
    return config


class simple_memoize:
    def __init__(self, fn):
        self.fn = fn
        self.cache = None

    def __call__(self):
        if self.cache is None:
            self.cache = self.fn()
        return self.cache


get_app_config = simple_memoize(read_app_config)
