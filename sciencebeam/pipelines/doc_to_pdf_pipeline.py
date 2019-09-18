import logging

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline

from .doc_to_type_pipeline import DocToTypeStep


LOGGER = logging.getLogger(__name__)


class DocToPdfStep(DocToTypeStep):
    def __init__(self):
        super().__init__(
            output_ext='.pdf',
            output_mime_type=MimeTypes.PDF
        )


class DocToPdfPipeline(Pipeline):
    def add_arguments(self, parser, config, argv=None):
        pass

    def get_steps(self, config, args):
        return [DocToPdfStep()]


PIPELINE = DocToPdfPipeline()
