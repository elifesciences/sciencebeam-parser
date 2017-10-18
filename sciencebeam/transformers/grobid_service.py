import logging

import requests
import six

NAME = __name__

PROCESS_HEADER_DOCUMENT_PATH = '/processHeaderDocument'

def grobid_service(base_url, path):
  url = base_url + path

  def do_grobid_service(x):
    logger = logging.getLogger(NAME)
    filename = x[0] if isinstance(x, tuple) else 'unknown.pdf'
    content = x[1] if isinstance(x, tuple) else x
    logger.info('processing: %s (%d) - %s', filename, len(content), url)
    response = requests.post(url,
      files={'input': (filename, six.StringIO(content))},
    )
    response.raise_for_status()
    result_content = response.content
    if isinstance(x, tuple):
      return filename, result_content
    else:
      return result_content
  return do_grobid_service
