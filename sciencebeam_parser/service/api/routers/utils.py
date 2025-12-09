import logging

from fastapi.responses import FileResponse

from sciencebeam_parser.app.parser import ScienceBeamParserSessionSource
from sciencebeam_parser.utils.media_types import MediaTypes


LOGGER = logging.getLogger(__name__)


def get_processed_source_to_response_media_type(
    source: ScienceBeamParserSessionSource,
    response_media_type: str
) -> FileResponse:
    LOGGER.debug('created session source: %r', source)
    LOGGER.debug('response_media_type: %r', response_media_type)
    actual_response_media_type = response_media_type
    if response_media_type in {
        MediaTypes.TEI_XML, MediaTypes.JATS_XML
    }:
        actual_response_media_type = MediaTypes.XML
    elif response_media_type in {
        MediaTypes.TEI_ZIP, MediaTypes.JATS_ZIP
    }:
        actual_response_media_type = MediaTypes.ZIP
    result_file = source.get_local_file_for_response_media_type(
        response_media_type
    )
    LOGGER.debug('result_file: %r', result_file)
    assert isinstance(result_file, str)
    return FileResponse(
        result_file,
        media_type=actual_response_media_type
    )
