import logging
import os
from subprocess import check_output
from backports.tempfile import TemporaryDirectory

from sciencebeam.utils.mime_type_constants import MimeTypes

LOGGER = logging.getLogger(__name__)

def doc_to_pdf(doc_content, data_type=MimeTypes.DOC):
  with TemporaryDirectory('doc-to-pdf') as path:
    doc_ext = '.docx' if data_type == MimeTypes.DOCX else '.doc'
    temp_doc = os.path.join(path, 'temp%s' % doc_ext)
    temp_pdf = os.path.join(path, 'temp.pdf')
    LOGGER.info('temp_doc: %s', temp_doc)
    with open(temp_doc, 'wb') as f:
      f.write(doc_content)
    check_output(['lowriter', '--convert-to', 'pdf', '--outdir', path, temp_doc])
    with open(temp_pdf, 'rb') as f:
      content = f.read()
      LOGGER.debug('read %d bytes (%s)', len(content), temp_pdf)
      return content
