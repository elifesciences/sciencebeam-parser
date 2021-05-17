from configparser import ConfigParser
from typing import Dict


def dict_to_config(d: Dict[str, Dict[str, str]]) -> ConfigParser:
    config = ConfigParser()
    for section in d.keys():
        config.add_section(section)
        for key, value in d[section].items():
            config.set(str(section), str(key), str(value))
    return config


def parse_list(s, sep=','):
    s = s.strip()
    if not s:
        return []
    return [item.strip() for item in s.split(sep)]
