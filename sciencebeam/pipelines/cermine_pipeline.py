import argparse  # pylint: disable=unused-import

import requests

from sciencebeam_utils.utils.file_path import change_ext

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline, RequestsPipelineStep


class CermineApiStep(RequestsPipelineStep):
    def get_supported_types(self):
        return {MimeTypes.PDF}

    def process_request(self, data: dict, session: requests.Session, context: dict = None):
        response = self.post_data(
            data=data,
            session=session,
            timeout=self.get_default_request_timeout(context=context)
        )
        return {
            'filename': change_ext(data['filename'], None, '.xml'),
            'content': response.text,
            'type': response.headers['Content-Type']
        }

    def __str__(self):
        return 'Cermine API'


class CerminePipeline(Pipeline):
    def add_arguments(self, parser, config, argv=None):
        # type: (argparse.ArgumentParser, dict, object) -> None
        cermine_group = parser.add_argument_group('Cermine')
        cermine_group.add_argument(
            '--cermine-url', required=True,
            help='URL to the Cermine service (e.g. http://cermine.ceon.pl/extract.do)'
        )

    def get_steps(self, config, args):
        # type: (dict, object) -> list
        steps = [
            CermineApiStep(args.cermine_url)
        ]
        return steps


PIPELINE = CerminePipeline()
