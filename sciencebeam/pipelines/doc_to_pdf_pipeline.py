import logging

from sciencebeam_gym.preprocess.preprocessing_utils import change_ext

from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam.transformers.doc_to_pdf import doc_to_pdf

from . import Pipeline, PipelineStep

LOGGER = logging.getLogger(__name__)

class DocToPdfStep(PipelineStep):
  def get_supported_types(self):
    return {MimeTypes.DOC, MimeTypes.DOCX, MimeTypes.DOTX, MimeTypes.RTF}

  def __call__(self, data):
    return {
      'filename': change_ext(data['filename'], None, '.pdf'),
      'content': doc_to_pdf(data['content'], data['type']),
      'type': MimeTypes.PDF
    }

  def __str__(self):
    return 'DOC to PDF'

  def __repr__(self):
    return '%s(%s)' % (type(self).__name__, str(self))

class DocToPdfPipeline(Pipeline):
  def add_arguments(self, parser, config, argv=None):
    pass

  def get_steps(self, config, args):
    return [DocToPdfStep()]

PIPELINE = DocToPdfPipeline()
