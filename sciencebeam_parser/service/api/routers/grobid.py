import logging
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from sciencebeam_parser.app.parser import ScienceBeamParserSessionSource
from sciencebeam_parser.processors.fulltext.config import FullTextProcessorConfig
from sciencebeam_parser.service.api.dependencies import (
    assert_and_get_first_accept_matching_media_type_factory,
    get_sciencebeam_parser_session_source_dependency_factory
)
from sciencebeam_parser.utils.media_types import MediaTypes


LOGGER = logging.getLogger(__name__)


TEI_XML_CONTENT_DOC = {
    "schema": {"type": "string", "format": "xml"},
    "example": "<TEI>...</TEI>"
}


JATS_XML_CONTENT_DOC = {
    "schema": {"type": "string", "format": "xml"},
    "example": "<article>...</article>"
}


TEI_AND_JATS_XML_CONTENT_DOC = {
    MediaTypes.TEI_XML: TEI_XML_CONTENT_DOC,
    MediaTypes.JATS_XML: JATS_XML_CONTENT_DOC
}


def get_processed_source_to_response_media_type(
    source: ScienceBeamParserSessionSource,
    response_media_type: str
) -> FileResponse:
    LOGGER.debug('created session source: %r', source)
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


def create_grobid_router(
    fulltext_processor_config: FullTextProcessorConfig
) -> APIRouter:
    router = APIRouter(tags=['grobid'])

    @router.post(
        '/processHeaderDocument',
        response_class=FileResponse,
        responses={
            200: {"content": TEI_AND_JATS_XML_CONTENT_DOC},
            406: {"description": "No acceptable media type"},
        },
    )
    def process_header_document_api(
        source: Annotated[
            ScienceBeamParserSessionSource,
            Depends(
                get_sciencebeam_parser_session_source_dependency_factory(
                    fulltext_processor_config=fulltext_processor_config.get_for_header_document()
                )
            )
        ],
        response_media_type: Annotated[
            str,
            Depends(
                assert_and_get_first_accept_matching_media_type_factory(
                    [MediaTypes.TEI_XML, MediaTypes.JATS_XML]
                )
            )
        ],
    ) -> FileResponse:
        return get_processed_source_to_response_media_type(
            source=source,
            response_media_type=response_media_type
        )

    return router
