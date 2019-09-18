import logging
import os
from backports.tempfile import TemporaryDirectory

from sciencebeam.utils.mime_type_constants import MimeTypes, guess_extension

from .doc_converter_wrapper import DocConverterWrapper


LOGGER = logging.getLogger(__name__)


OUTPUT_TYPE_BY_MIME_TYPE = {
    MimeTypes.DOCX: 'docx',
    MimeTypes.PDF: 'pdf'
}


DEFAULT_CONFIGURATION = dict(
    enable_debug=False,
    # Note: we tell the conversion not to start the uno service,
    #   because we will start it ahead of time
    no_launch=True,
    keep_listener_running=True,
    process_timeout=60
)

_STATE = {
    'config': DEFAULT_CONFIGURATION
}


def _get_doc_converter() -> DocConverterWrapper:
    instance = _STATE.get('instance')
    if instance is None:
        config = _STATE.get('config', DEFAULT_CONFIGURATION)
        instance = DocConverterWrapper(**config)
        _STATE['instance'] = instance
    return instance


def _convert_doc_to(doc_content, data_type, output_type, **kwargs):
    with TemporaryDirectory('convert-doc-to') as path:
        doc_ext = guess_extension(data_type)
        temp_doc = os.path.join(path, 'temp%s' % doc_ext)
        LOGGER.info('temp_doc: %s', temp_doc)
        with open(temp_doc, 'wb') as f:
            f.write(doc_content)
        doc_converter = _get_doc_converter()
        temp_out = doc_converter.convert(temp_doc, output_type=output_type, **kwargs)
        with open(temp_out, 'rb') as f:
            content = f.read()
            LOGGER.debug('read %d bytes (%s)', len(content), temp_out)
            return content


def doc_to_pdf(doc_content, data_type=MimeTypes.DOC, **kwargs):
    return _convert_doc_to(doc_content, data_type, 'pdf', **kwargs)


def doc_to_docx(doc_content, data_type=MimeTypes.DOC, **kwargs):
    return _convert_doc_to(doc_content, data_type, 'docx', **kwargs)


def doc_to_type(
        doc_content,
        data_type: str,
        output_mime_type: str,
        **kwargs):
    output_type = OUTPUT_TYPE_BY_MIME_TYPE[output_mime_type]
    return _convert_doc_to(doc_content, data_type, output_type, **kwargs)
