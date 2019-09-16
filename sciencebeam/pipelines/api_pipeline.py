import logging

import requests

from sciencebeam_utils.utils.file_path import change_ext

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline, RequestsPipelineStep

LOGGER = logging.getLogger(__name__)


class ApiStep(RequestsPipelineStep):
    def get_supported_types(self):
        return {MimeTypes.DOC, MimeTypes.DOCX, MimeTypes.DOTX, MimeTypes.RTF, MimeTypes.PDF}

    def process_request(self, data: dict, session: requests.Session):
        response = self.post_data(
            data=data,
            session=session,
            params={'filename': data['filename']}
        )
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
