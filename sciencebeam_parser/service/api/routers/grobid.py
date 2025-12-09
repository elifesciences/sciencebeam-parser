import logging
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from sciencebeam_parser.app.parser import ScienceBeamParserSessionSource
from sciencebeam_parser.processors.fulltext.config import FullTextProcessorConfig
from sciencebeam_parser.service.api.dependencies import (
    get_sciencebeam_parser_session_source_dependency_factory
)
from sciencebeam_parser.utils.media_types import MediaTypes


LOGGER = logging.getLogger(__name__)


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

    @router.post('/processHeaderDocument', response_class=FileResponse)
    def process_header_document_api(
        source: Annotated[
            ScienceBeamParserSessionSource,
            Depends(
                get_sciencebeam_parser_session_source_dependency_factory(
                    fulltext_processor_config=fulltext_processor_config.get_for_header_document()
                )
            )
        ]
    ) -> FileResponse:
        return get_processed_source_to_response_media_type(
            source=source,
            response_media_type=MediaTypes.TEI_XML
        )

    return router
