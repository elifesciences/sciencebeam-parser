import logging
import os
from distutils.util import strtobool
from backports.tempfile import TemporaryDirectory

from sciencebeam.config.app_config import get_app_config
from sciencebeam.utils.mime_type_constants import MimeTypes, guess_extension

from .doc_converter_wrapper import DocConverterWrapper


LOGGER = logging.getLogger(__name__)


OUTPUT_TYPE_BY_MIME_TYPE = {
    MimeTypes.DOCX: 'docx',
    MimeTypes.PDF: 'pdf'
}


DOC_CONVERT_SECTION_NAME = 'doc_convert'


class AppConfigOptions:
    STOP_LISTENER_ON_ERROR = 'stop_listener_on_error'
    PROCESS_TIMEOUT = 'process_timeout'
    MAX_UPTIME = 'max_uptime'
    ENABLE_DEBUG = 'enable_debug'


class EnvironmentVariables:
    DOC_CONVERT_PROCESS_TIMEOUT = 'SCIENCEBEAM_DOC_CONVERT_PROCESS_TIMEOUT'
    DOC_CONVERT_MAX_UPTIME = 'SCIENCEBEAM_DOC_CONVERT_MAX_UPTIME'
    DOC_CONVERT_ENABLE_DEBUG = 'SCIENCEBEAM_DOC_CONVERT_ENABLE_DEBUG'


DEFAULT_DOC_CONVERT_PROCESS_TIMEOUT = 5 * 60  # 5 minutes
DEFAULT_DOC_CONVERT_MAX_UPTIME = 24 * 60 * 60  # 24 hours


DEFAULT_CONFIGURATION = dict(
    enable_debug=False,
    # Note: we tell the conversion not to start the uno service,
    #   because we will start it ahead of time
    no_launch=True,
    keep_listener_running=True,
    process_timeout=DEFAULT_DOC_CONVERT_PROCESS_TIMEOUT
)


_STATE = {
}


def _get_default_config():
    config = DEFAULT_CONFIGURATION
    app_config = get_app_config()
    process_timeout = os.environ.get(EnvironmentVariables.DOC_CONVERT_PROCESS_TIMEOUT)
    if not process_timeout:
        process_timeout = app_config.getint(
            DOC_CONVERT_SECTION_NAME, AppConfigOptions.PROCESS_TIMEOUT,
            fallback=DEFAULT_DOC_CONVERT_PROCESS_TIMEOUT
        )
    max_uptime = os.environ.get(EnvironmentVariables.DOC_CONVERT_MAX_UPTIME)
    if not max_uptime:
        max_uptime = app_config.getint(
            DOC_CONVERT_SECTION_NAME, AppConfigOptions.MAX_UPTIME,
            fallback=DEFAULT_DOC_CONVERT_MAX_UPTIME
        )
    enable_debug = os.environ.get(EnvironmentVariables.DOC_CONVERT_ENABLE_DEBUG)
    if enable_debug:
        enable_debug = bool(strtobool(enable_debug))
    else:
        enable_debug = app_config.getboolean(
            DOC_CONVERT_SECTION_NAME, AppConfigOptions.ENABLE_DEBUG,
            fallback=DEFAULT_CONFIGURATION['enable_debug']
        )
    config = {
        **config,
        'process_timeout': int(process_timeout),
        'max_uptime': int(max_uptime),
        'stop_listener_on_error': app_config.getboolean(
            DOC_CONVERT_SECTION_NAME, AppConfigOptions.STOP_LISTENER_ON_ERROR
        ),
        'enable_debug': enable_debug
    }
    return config


def _get_config():
    config = _STATE.get('config')
    if not config:
        config = _get_default_config()
    return config


def _get_doc_converter() -> DocConverterWrapper:
    instance = _STATE.get('instance')
    if instance is None:
        config = _get_config()
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
