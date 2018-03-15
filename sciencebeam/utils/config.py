from configparser import ConfigParser

from six import text_type

def dict_to_config(d):
  config = ConfigParser()
  for section in d.keys():
    config.add_section(section)
    for key, value in d[section].items():
      config.set(text_type(section), text_type(key), text_type(value))
  return config
