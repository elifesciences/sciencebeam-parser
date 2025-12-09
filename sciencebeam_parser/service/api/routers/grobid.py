import logging
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from sciencebeam_parser.app.parser import ScienceBeamParserSessionSource
from sciencebeam_parser.processors.fulltext.config import FullTextProcessorConfig, RequestFieldNames
from sciencebeam_parser.service.api.dependencies import (
    assert_and_get_first_accept_matching_media_type_factory,
    get_sciencebeam_parser_session_source_dependency_factory
)
from sciencebeam_parser.service.api.routers.docs import (
    TEI_AND_JATS_XML_CONTENT_DOC,
    TEI_AND_JATS_ZIP_CONTENT_DOC
)
from sciencebeam_parser.service.api.routers.utils import get_processed_source_to_response_media_type
from sciencebeam_parser.utils.media_types import MediaTypes


LOGGER = logging.getLogger(__name__)


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

    @router.post(
        '/processFulltextDocument',
        response_class=FileResponse,
        responses={
            200: {"content": TEI_AND_JATS_XML_CONTENT_DOC},
            406: {"description": "No acceptable media type"},
        },
    )
    def process_fulltext_document_api(
        source: Annotated[
            ScienceBeamParserSessionSource,
            Depends(
                get_sciencebeam_parser_session_source_dependency_factory(
                    fulltext_processor_config=fulltext_processor_config
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

    @router.post(
        '/processReferences',
        response_class=FileResponse,
        responses={
            200: {"content": TEI_AND_JATS_XML_CONTENT_DOC},
            406: {"description": "No acceptable media type"},
        },
    )
    def process_references_api(
        source: Annotated[
            ScienceBeamParserSessionSource,
            Depends(
                get_sciencebeam_parser_session_source_dependency_factory(
                    fulltext_processor_config=(
                        fulltext_processor_config
                        .get_for_requested_field_names({
                            RequestFieldNames.REFERENCES
                        })
                    )
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

    @router.post(
        '/processFulltextAssetDocument',
        response_class=FileResponse,
        responses={
            200: {"content": TEI_AND_JATS_ZIP_CONTENT_DOC},
            406: {"description": "No acceptable media type"},
        },
    )
    def process_pdf_to_tei_assets_zip(
        source: Annotated[
            ScienceBeamParserSessionSource,
            Depends(
                get_sciencebeam_parser_session_source_dependency_factory(
                    fulltext_processor_config=fulltext_processor_config
                )
            )
        ],
        response_media_type: Annotated[
            str,
            Depends(
                assert_and_get_first_accept_matching_media_type_factory(
                    [MediaTypes.TEI_ZIP, MediaTypes.JATS_ZIP]
                )
            )
        ],
    ) -> FileResponse:
        return get_processed_source_to_response_media_type(
            source=source,
            response_media_type=response_media_type
        )

    return router
