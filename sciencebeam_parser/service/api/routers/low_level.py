import logging
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from sciencebeam_parser.app.parser import ScienceBeamParserSessionSource
from sciencebeam_parser.service.api.dependencies import (
    get_sciencebeam_parser_session_source_dependency_factory
)
from sciencebeam_parser.utils.media_types import MediaTypes


LOGGER = logging.getLogger(__name__)


class AltoXmlFileResponse(FileResponse):
    media_type = MediaTypes.ALTO_XML


def create_low_level_router() -> APIRouter:
    router = APIRouter(tags=['low-level'])

    @router.post('/pdfalto', response_class=AltoXmlFileResponse)
    def pdfalto(
        source: Annotated[
            ScienceBeamParserSessionSource,
            Depends(
                get_sciencebeam_parser_session_source_dependency_factory()
            )
        ]
    ) -> AltoXmlFileResponse:
        return AltoXmlFileResponse(
            path=source.get_local_file_for_response_media_type(
                MediaTypes.ALTO_XML
            ),
            media_type=AltoXmlFileResponse.media_type
        )

    return router
