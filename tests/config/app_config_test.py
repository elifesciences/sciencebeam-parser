from io import StringIO
import logging
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from sciencebeam.utils.config import dict_to_config

from sciencebeam.config import app_config as app_config_module
from sciencebeam.config.app_config import (
    get_app_config_filename,
    get_app_defaults_config_filename,
    read_app_config
)

LOGGER = logging.getLogger(__name__)

SECTION_1 = u'section1'
SECTION_2 = u'section2'
KEY_1 = u'key1'
KEY_2 = u'key2'
VALUE_1 = u'value1'
VALUE_2 = u'value2'


@pytest.fixture(name='get_app_root_mock')
def _get_app_root_mock():
    with patch.object(app_config_module, 'get_app_root') as mock:
        yield mock


class TestGetAppConfigFilename:
    def test_should_end_with_app_cfg(self):
        assert get_app_config_filename().endswith('app.cfg')

    def test_should_exist(self):
        assert os.path.isfile(get_app_defaults_config_filename())


class TestGetAppDefaultsConfigFilename:
    def test_should_end_with_app_defaults_cfg(self):
        assert get_app_defaults_config_filename().endswith('app-defaults.cfg')

    def test_should_exist(self):
        assert os.path.isfile(get_app_defaults_config_filename())


def _dict_to_cfg_content(d):
    config = dict_to_config(d)
    fp = StringIO()
    config.write(fp)
    content = fp.getvalue()
    LOGGER.debug('content: %s', content)
    return content


class TestReadAppConfig:
    def test_should_read_actual_config(self):
        assert read_app_config()

    def test_should_override_config_with_app_cfg(self, tmpdir):
        tmpdir.join('app-defaults.cfg').write(_dict_to_cfg_content({
            SECTION_1: {KEY_1: VALUE_1}
        }))
        tmpdir.join('app.cfg').write(_dict_to_cfg_content({
            SECTION_1: {KEY_1: VALUE_2}
        }))
        m = app_config_module
        with patch.object(m, 'get_app_root') as get_app_root_mock:
            get_app_root_mock.return_value = str(tmpdir)
            app_config = read_app_config()
            assert app_config.get(SECTION_1, KEY_1) == VALUE_2

    def test_should_return_defaults_from_same_section_if_not_overridden(self, tmpdir):
        tmpdir.join('app-defaults.cfg').write(_dict_to_cfg_content({
            SECTION_1: {KEY_1: VALUE_1}
        }))
        tmpdir.join('app.cfg').write(_dict_to_cfg_content({
            SECTION_1: {KEY_2: VALUE_2}
        }))
        m = app_config_module
        with patch.object(m, 'get_app_root') as get_app_root_mock:
            get_app_root_mock.return_value = str(tmpdir)
            app_config = read_app_config()
            assert app_config.get(SECTION_1, KEY_1) == VALUE_1
            assert app_config.get(SECTION_1, KEY_2) == VALUE_2

    def test_should_return_defaults_from_another_section_if_not_overridden(self, tmpdir):
        tmpdir.join('app-defaults.cfg').write(_dict_to_cfg_content({
            SECTION_1: {KEY_1: VALUE_1}
        }))
        tmpdir.join('app.cfg').write(_dict_to_cfg_content({
            SECTION_2: {KEY_2: VALUE_2}
        }))
        m = app_config_module
        with patch.object(m, 'get_app_root') as get_app_root_mock:
            get_app_root_mock.return_value = str(tmpdir)
            app_config = read_app_config()
            assert app_config.get(SECTION_1, KEY_1) == VALUE_1
            assert app_config.get(SECTION_2, KEY_2) == VALUE_2

    @patch.object(os, 'environ', {})
    def test_should_override_with_environment_variables(
            self, temp_dir: Path,
            get_app_root_mock: MagicMock):
        temp_dir.joinpath('app-defaults.cfg').write_text(_dict_to_cfg_content({
            SECTION_1: {KEY_1: VALUE_1}
        }))
        get_app_root_mock.return_value = str(temp_dir)
        os.environ['__'.join(['SCIENCEBEAM', SECTION_1, KEY_1]).upper()] = VALUE_2
        app_config = read_app_config()
        assert app_config.get(SECTION_1, KEY_1) == VALUE_2
