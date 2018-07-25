from requests import post as requests_post

from sciencebeam_gym.preprocess.preprocessing_utils import change_ext

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline, PipelineStep

class MeTypesetApiStep(PipelineStep):
  def __init__(self, api_url):
    self._api_url = api_url

  def get_supported_types(self):
    return {MimeTypes.DOCX}

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
    return 'meTypeset API'

  def __repr__(self):
    return '%s(%s)' % (type(self).__name__, self._api_url)

class MeTypesetPipeline(Pipeline):
  def add_arguments(self, parser, config, argv=None):
    # type: (argparse.ArgumentParser, dict, object) -> None
    metypeset_group = parser.add_argument_group('meTypeset')
    metypeset_group.add_argument(
      '--metypeset-url', required=True,
      help='URL to the meTypeset service (e.g. http://metypeset:8074/api/convert)'
    )

  def get_steps(self, config, args):
    # type: (dict, object) -> list
    steps = [
      MeTypesetApiStep(args.metypeset_url)
    ]
    return steps

PIPELINE = MeTypesetPipeline()
