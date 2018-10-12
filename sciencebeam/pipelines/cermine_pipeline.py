from requests import post as requests_post

from sciencebeam_utils.utils.file_path import change_ext

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline, PipelineStep


class CermineApiStep(PipelineStep):
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
