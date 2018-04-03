import logging

import requests
import six

from sciencebeam.transformers.grobid_service_wrapper import (
  GrobidServiceWrapper
)

class GrobidApiPaths(object):
  PROCESS_HEADER_DOCUMENT = '/processHeaderDocument'
  PROCESS_HEADER_NAMES = '/processHeaderNames'
  PROCESS_CITATION_NAMES = '/processCitationNames'
  PROCESS_AFFILIATIONS = '/processAffiliations'
  PROCESS_CITATION = '/processCitation'

service_wrapper = GrobidServiceWrapper()

def get_logger():
  return logging.getLogger(__name__)

def start_service_if_not_running():
  service_wrapper.start_service_if_not_running()

def grobid_service(base_url, path, start_service=True, field_name=None):
  url = base_url + path

  def do_grobid_service(x):
    if start_service:
      start_service_if_not_running()
    if field_name:
      content = x
      response = requests.post(url,
        data={field_name: content}
      )
    else:
      filename = x[0] if isinstance(x, tuple) else 'unknown.pdf'
      content = x[1] if isinstance(x, tuple) else x
      get_logger().info('processing: %s (%d) - %s', filename, len(content), url)
      response = requests.post(url,
        files={'input': (filename, six.StringIO(content))},
        data={
          'consolidateHeader': '0',
          'consolidateCitations': '0'
        }
      )
    response.raise_for_status()
    result_content = response.content
    if isinstance(x, tuple):
      return filename, result_content
    else:
      return result_content
  return do_grobid_service
