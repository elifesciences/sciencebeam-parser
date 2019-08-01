import json
import logging
from typing import Union

from dicttoxml import dicttoxml


logging.getLogger('dicttoxml').setLevel('WARN')


def json_to_xml(json_content: Union[bytes, str]):
    if isinstance(json_content, bytes):
        json_content = json_content.decode('utf-8')
    return dicttoxml(json.loads(json_content))
