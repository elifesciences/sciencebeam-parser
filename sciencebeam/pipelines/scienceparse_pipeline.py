from requests import post as requests_post

from sciencebeam_utils.utils.file_path import change_ext

from sciencebeam.transformers.xslt import xslt_transformer_from_file
from sciencebeam.transformers.json_to_xml import json_to_xml

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline, PipelineStep, FunctionPipelineStep

DEFAULT_SCIENCE_PARSE_XSLT_PATH = 'xslt/scienceparse-jats.xsl'

class ScienceParseApiStep(PipelineStep):
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
    return 'Science Parse API'

  def __repr__(self):
    return '%s(%s)' % (type(self).__name__, self._api_url)

class ScienceParsePipeline(Pipeline):
  def add_arguments(self, parser, config, argv=None):
    # type: (argparse.ArgumentParser, dict, object) -> None
    science_parse_group = parser.add_argument_group('Science Parse / Science Parse V2')
    science_parse_group.add_argument(
      '--science-parse-url', required=True,
      help='URL to the Science Parse service'
    )
    science_parse_group.add_argument(
      '--no-science-parse-xslt', action='store_true',
      help='Disable translation using XSLT'
    )
    science_parse_group.add_argument(
      '--science-parse-xslt-path', default=DEFAULT_SCIENCE_PARSE_XSLT_PATH,
      help='Path to XSLT file translating results to JATS'
    )
    science_parse_group.add_argument(
      '--no-science-parse-pretty-print', action='store_true',
      help='Disable pretty print of XSLT output'
    )

  def get_steps(self, config, args):
    # type: (dict, object) -> list
    steps = [
      ScienceParseApiStep(args.science_parse_url)
    ]
    if not args.no_science_parse_xslt:
      xslt_transformer = xslt_transformer_from_file(
        args.science_parse_xslt_path,
        pretty_print=not args.no_science_parse_pretty_print
      )
      steps.append(FunctionPipelineStep(lambda d: {
        'content': xslt_transformer(json_to_xml(d['content'])),
        'type': MimeTypes.JATS_XML
      }, {MimeTypes.JSON}, 'Science Parse to JATS'))
    return steps

PIPELINE = ScienceParsePipeline()
