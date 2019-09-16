import argparse  # pylint: disable=unused-import

import requests

from sciencebeam_utils.utils.file_path import change_ext

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline, RequestsPipelineStep


class ContentMineApiStep(RequestsPipelineStep):
    def get_supported_types(self):
        return {MimeTypes.PDF}

    def process_request(self, data: dict, session: requests.Session):
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
        return 'ContentMine API'


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
