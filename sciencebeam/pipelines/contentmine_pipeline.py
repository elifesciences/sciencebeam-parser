from requests import post as requests_post

from sciencebeam_gym.preprocess.preprocessing_utils import change_ext

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline, PipelineStep

class ContentMineApiStep(PipelineStep):
  def __init__(self, api_url):
    self._api_url = api_url

  def get_supported_types(self):
    return {MimeTypes.PDF}

  def __call__(self, data):
    response = requests_post(
      self._api_url,
      headers={'Content-Type': data['type']},
      data=data['content']
    )
    response.raise_for_status()
    return {
      'filename': change_ext(data['filename'], None, '.xml'),
      'content': response.text,
      'type': response.headers['Content-Type']
    }

  def __str__(self):
    return 'Cermine API'

  def __repr__(self):
    return '%s(%s)' % (type(self).__name__, self._api_url)

class ContentMinePipeline(Pipeline):
  def add_arguments(self, parser, config, argv=None):
    # type: (argparse.ArgumentParser, dict, object) -> None
    contentmine_group = parser.add_argument_group('ContentMine')
    contentmine_group.add_argument(
      '--contentmine-url', required=True,
      help='URL to the ContentMine service (e.g. http://contentmine:8076/api/convert)'
    )

  def get_steps(self, config, args):
    # type: (dict, object) -> list
    steps = [
      ContentMineApiStep(args.contentmine_url)
    ]
    return steps

PIPELINE = ContentMinePipeline()
