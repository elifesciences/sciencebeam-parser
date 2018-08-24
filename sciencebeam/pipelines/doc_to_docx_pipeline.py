import logging

from sciencebeam_utils.utils.file_path import change_ext

from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam.transformers.convert_doc import doc_to_docx

from . import Pipeline, PipelineStep

LOGGER = logging.getLogger(__name__)

class DocToDocxStep(PipelineStep):
  def get_supported_types(self):
    return {MimeTypes.DOC, MimeTypes.DOCX, MimeTypes.DOTX, MimeTypes.RTF}

  def __call__(self, data):
    return {
      'filename': change_ext(data['filename'], None, '.docx'),
      'content': doc_to_docx(data['content'], data['type']),
      'type': MimeTypes.DOCX
    }

  def __str__(self):
    return 'DOC to DOCX'

  def __repr__(self):
    return '%s(%s)' % (type(self).__name__, str(self))

class DocToDocxPipeline(Pipeline):
  def add_arguments(self, parser, config, argv=None):
    pass

  def get_steps(self, config, args):
    return [DocToDocxStep()]

PIPELINE = DocToDocxPipeline()
