import json
import logging

from dicttoxml import dicttoxml

logging.getLogger('dicttoxml').setLevel('WARN')


def json_to_xml(json_content):
    return dicttoxml(json.loads(json_content))
