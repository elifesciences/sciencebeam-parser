import argparse  # pylint: disable=unused-import

import requests

from sciencebeam_utils.utils.file_path import change_ext

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline, RequestsPipelineStep


class MeTypesetApiStep(RequestsPipelineStep):
    def get_supported_types(self):
        return {MimeTypes.DOCX}

    def process_request(self, data: dict, session: requests.Session, context: dict = None):
        response = self.post_data(
            data=data,
            session=session
        )
        return {
            'filename': change_ext(data['filename'], None, '.xml'),
            'content': response.text,
            'type': response.headers['Content-Type']
        }

    def __str__(self):
        return 'meTypeset API'


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
