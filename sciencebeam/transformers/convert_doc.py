import logging
import os
from subprocess import check_output
from backports.tempfile import TemporaryDirectory

from sciencebeam.utils.mime_type_constants import MimeTypes, guess_extension


LOGGER = logging.getLogger(__name__)


def _convert_doc_to(doc_content, data_type, output_type):
    with TemporaryDirectory('convert-doc-to') as path:
        doc_ext = guess_extension(data_type)
        temp_doc = os.path.join(path, 'temp%s' % doc_ext)
        temp_out = os.path.join(path, 'temp.%s' % output_type)
        LOGGER.info('temp_doc: %s', temp_doc)
        with open(temp_doc, 'wb') as f:
            f.write(doc_content)
        check_output([
            'lowriter',
            '--convert-to', output_type,
            '--outdir', path, temp_doc
        ])
        with open(temp_out, 'rb') as f:
            content = f.read()
            LOGGER.debug('read %d bytes (%s)', len(content), temp_out)
            return content


def doc_to_pdf(doc_content, data_type=MimeTypes.DOC):
    return _convert_doc_to(doc_content, data_type, 'pdf')


def doc_to_docx(doc_content, data_type=MimeTypes.DOC):
    return _convert_doc_to(doc_content, data_type, 'docx')
