import logging

from sciencebeam_utils.utils.file_path import change_ext

from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam.transformers.convert_doc import doc_to_type

from . import PipelineStep

LOGGER = logging.getLogger(__name__)


class DocToTypeStep(PipelineStep):
    def __init__(
            self, output_ext: str, output_mime_type: str):
        self.output_ext = output_ext
        self.output_mime_type = output_mime_type

    def get_supported_types(self):
        return {MimeTypes.DOC, MimeTypes.DOCX, MimeTypes.DOTX, MimeTypes.RTF}

    def __call__(self, data, context: dict = None):
        return {
            'filename': change_ext(data['filename'], None, self.output_ext),
            'content': doc_to_type(
                data['content'],
                data['type'],
                output_mime_type=self.output_mime_type
            ),
            'type': self.output_mime_type
        }

    def __str__(self):
        return 'DOC to %s' % self.output_ext

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, str(self))
