import os
from io import BytesIO
import logging
from functools import partial
from typing import Dict

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


class GrobidServiceConfigEnvVariables:
    CONSOLIDATE_HEADER = 'SCIENCEBEAM_CONSOLIDATE_HEADER'
    CONSOLIDATE_CITATIONS = 'SCIENCEBEAM_CONSOLIDATE_CITATIONS'
    INCLUDE_RAW_AFFILIATIONS = 'SCIENCEBEAM_INCLUDE_RAW_AFFILIATIONS'
    INCLUDE_RAW_CITATIONS = 'SCIENCEBEAM_INCLUDE_RAW_CITATIONS'


service_wrapper = GrobidServiceWrapper()


def get_logger():
    return logging.getLogger(__name__)


class GrobidServiceConfig:
    def __init__(
            self,
            consolidate_header: bool = False,
            consolidate_citations: bool = False,
            include_raw_affiliations: bool = True,
            include_raw_citations: bool = True):
        self.consolidate_header = consolidate_header
        self.consolidate_citations = consolidate_citations
        self.include_raw_affiliations = include_raw_affiliations
        self.include_raw_citations = include_raw_citations


def get_grobid_service_config() -> GrobidServiceConfig:
    env_to_prop_map = {
        GrobidServiceConfigEnvVariables.CONSOLIDATE_HEADER: 'consolidate_header',
        GrobidServiceConfigEnvVariables.CONSOLIDATE_CITATIONS: 'consolidate_citations',
        GrobidServiceConfigEnvVariables.INCLUDE_RAW_AFFILIATIONS: 'include_raw_affiliations',
        GrobidServiceConfigEnvVariables.INCLUDE_RAW_CITATIONS: 'include_raw_citations'
    }
    config = GrobidServiceConfig()
    for env_name, prop_name in env_to_prop_map.items():
        env_value = os.environ.get(env_name)
        if env_value:
            setattr(config, prop_name, env_value == '1')
    return config


def _get_bool_int_param(bool_value: bool) -> str:
    return '1' if bool_value else '0'


def get_request_data_for_config(grobid_service_config: GrobidServiceConfig) -> Dict[str, str]:
    return {
        'consolidateHeader': _get_bool_int_param(
            grobid_service_config.consolidate_header
        ),
        'consolidateCitations': _get_bool_int_param(
            grobid_service_config.consolidate_citations
        ),
        'includeRawAffiliations': _get_bool_int_param(
            grobid_service_config.include_raw_affiliations
        ),
        'includeRawCitations': _get_bool_int_param(
            grobid_service_config.include_raw_citations
        )
    }


def start_service_if_not_running():
    service_wrapper.start_service_if_not_running()


def run_grobid_service(
        item,
        base_url: str,
        path: str,
        grobid_service_config: GrobidServiceConfig = None,
        start_service: bool = True,
        field_name: str = None):
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
            data=get_request_data_for_config(grobid_service_config)
        )
    response.raise_for_status()
    result_content = response.content
    if isinstance(item, tuple):
        return filename, result_content
    return result_content


def grobid_service(
        base_url: str,
        path: str,
        start_service: bool = True,
        field_name: str = None,
        grobid_service_config: GrobidServiceConfig = None):
    if not grobid_service_config:
        grobid_service_config = get_grobid_service_config()
    return partial(
        run_grobid_service,
        base_url=base_url,
        path=path,
        start_service=start_service,
        field_name=field_name,
        grobid_service_config=grobid_service_config
    )
