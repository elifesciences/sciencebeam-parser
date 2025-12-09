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
from sciencebeam_parser.service.api.routers.docs import (
    PDF_CONTENT_DOC,
    TEI_AND_JATS_XML_CONTENT_DOC,
    TEI_AND_JATS_ZIP_CONTENT_DOC
)
from sciencebeam_parser.service.api.routers.utils import get_processed_source_to_response_media_type
from sciencebeam_parser.utils.media_types import MediaTypes


LOGGER = logging.getLogger(__name__)


def create_convert_router(
    fulltext_processor_config: FullTextProcessorConfig
) -> APIRouter:
    router = APIRouter(tags=['convert'])

    @router.post(
        '/convert',
        response_class=FileResponse,
        responses={
            200: {
                "content": {
                    **TEI_AND_JATS_XML_CONTENT_DOC,
                    **TEI_AND_JATS_ZIP_CONTENT_DOC,
                    MediaTypes.PDF: PDF_CONTENT_DOC
                }
            },
            406: {"description": "No acceptable media type"},
        },
    )
    def process_convert_api(
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
                    [
                        MediaTypes.JATS_XML, MediaTypes.TEI_XML,
                        MediaTypes.JATS_ZIP, MediaTypes.TEI_ZIP,
                        MediaTypes.PDF
                    ]
                )
            )
        ],
    ) -> FileResponse:
        return get_processed_source_to_response_media_type(
            source=source,
            response_media_type=response_media_type
        )

    return router
