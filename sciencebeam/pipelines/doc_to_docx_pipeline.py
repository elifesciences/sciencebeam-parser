import logging

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline

from .doc_to_type_pipeline import DocToTypeStep


LOGGER = logging.getLogger(__name__)


class DocToDocxStep(DocToTypeStep):
    def __init__(self):
        super().__init__(
            output_ext='.docx',
            output_mime_type=MimeTypes.DOCX
        )


class DocToDocxPipeline(Pipeline):
    def add_arguments(self, parser, config, argv=None):
        pass

    def get_steps(self, config, args):
        return [DocToDocxStep()]


PIPELINE = DocToDocxPipeline()
