from io import BytesIO
import logging
from functools import partial

import requests

from sciencebeam.transformers.grobid_service_wrapper import (
    GrobidServiceWrapper
)


class GrobidApiPaths:
    PROCESS_HEADER_DOCUMENT = '/processHeaderDocument'
    PROCESS_HEADER_NAMES = '/processHeaderNames'
    PROCESS_CITATION_NAMES = '/processCitationNames'
    PROCESS_AFFILIATIONS = '/processAffiliations'
    PROCESS_CITATION = '/processCitation'
    PROCESS_FULL_TEXT_DOCUMENT = '/processFulltextDocument'


service_wrapper = GrobidServiceWrapper()


def get_logger():
    return logging.getLogger(__name__)


def start_service_if_not_running():
    service_wrapper.start_service_if_not_running()


def run_grobid_service(item, base_url, path, start_service=True, field_name=None):
    """
    Translates PDF content via the GROBID service.

    Args:
      item: one of:
        * tuple (filename, pdf content)
        * pdf content
        * field content (requires field name)
      base_url: base url to the GROBID service
      path: path of the GROBID endpoint
      start_service: if true, a GROBID service will be started automatically and
        kept running until the application ends
      field_name: the field name the field content relates to

    Returns:
      If item is tuple:
        returns tuple (filename, xml result)
      Otherwise:
        returns xml result
    """

    url = base_url + path

    if start_service:
        start_service_if_not_running()

    if field_name:
        content = item
        response = requests.post(
            url,
            data={field_name: content}
        )
    else:
        filename = item[0] if isinstance(item, tuple) else 'unknown.pdf'
        content = item[1] if isinstance(item, tuple) else item
        get_logger().info('processing: %s (%d) - %s', filename, len(content), url)
        response = requests.post(
            url,
            files={'input': (filename, BytesIO(content))},
            data={
                'consolidateHeader': '0',
                'consolidateCitations': '0',
                'includeRawAffiliations': '1',
                'includeRawCitations': '1'
            }
        )
    response.raise_for_status()
    result_content = response.content
    if isinstance(item, tuple):
        return filename, result_content
    return result_content


def grobid_service(base_url, path, start_service=True, field_name=None):
    return partial(
        run_grobid_service,
        base_url=base_url,
        path=path,
        start_service=start_service,
        field_name=field_name
    )
