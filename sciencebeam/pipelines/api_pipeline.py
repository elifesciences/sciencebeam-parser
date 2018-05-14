import logging

import requests

from sciencebeam_gym.preprocess.preprocessing_utils import change_ext

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline, PipelineStep

LOGGER = logging.getLogger(__name__)

class ApiStep(PipelineStep):
  def __init__(self, api_url):
    self._api_url = api_url

  def get_supported_types(self):
    return {MimeTypes.DOC, MimeTypes.DOCX, MimeTypes.DOTX, MimeTypes.RTF, MimeTypes.PDF}

  def __call__(self, data):
    response = requests.post(
      self._api_url,
      headers={'Content-type': data['type']},
      data=data['content'],
      params={'filename': data['filename']}
    )
    response.raise_for_status()
    return {
      'filename': change_ext(data['filename'], None, '.xml'),
      'content': response.text,
      'type': response.headers['Content-Type']
    }

  def __str__(self):
    return 'API'

  def __repr__(self):
    return '%s(%s)' % (type(self).__name__, str(self))

class ApiPipeline(Pipeline):
  def add_arguments(self, parser, config, argv=None):
    api_group = parser.add_argument_group('API')
    api_group.add_argument(
      '--api-url', required=True,
      help='API URL to delegate requests too'
    )

  def get_steps(self, config, args):
    return [ApiStep(args.api_url)]

PIPELINE = ApiPipeline()
