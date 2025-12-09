import logging
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    Request
)
from fastapi.responses import JSONResponse


from sciencebeam_parser.app.parser import (
    ScienceBeamParser,
    ScienceBeamParserSessionSource,
    UnsupportedRequestMediaTypeScienceBeamParserError
)
from sciencebeam_parser.service.api.dependencies import (
    get_sciencebeam_parser_session_source_dependency_factory,
    get_media_data_wrapper
)
from sciencebeam_parser.service.api.routers.convert import create_convert_router
from sciencebeam_parser.service.api.routers.grobid import create_grobid_router
from sciencebeam_parser.service.api.routers.low_level import create_low_level_router
from sciencebeam_parser.utils.data_wrapper import MediaDataWrapper


LOGGER = logging.getLogger(__name__)


def create_api_app(
    sciencebeam_parser: ScienceBeamParser
) -> FastAPI:
    app = FastAPI()
    app.state.sciencebeam_parser = sciencebeam_parser

    app.include_router(create_low_level_router())
    app.include_router(create_grobid_router(
        fulltext_processor_config=sciencebeam_parser.fulltext_processor_config
    ))
    app.include_router(create_convert_router())

    @app.exception_handler(Exception)
    async def log_unhandled_exceptions(
        request: Request,
        exc: Exception  # pylint: disable=unused-argument
    ):
        LOGGER.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

    @app.exception_handler(Exception)
    async def handle_unsupported_request_media_type(
        request: Request,
        exc: UnsupportedRequestMediaTypeScienceBeamParserError  # pylint: disable=unused-argument
    ):
        LOGGER.info("Unsupported request media type: %s", exc)
        return JSONResponse(
            status_code=406,
            content={"detail": str(exc)},
        )

    @app.get('/')
    def api_root() -> dict:
        return {
            'links': {}
        }

    @app.post("/process")
    def process(
        media: MediaDataWrapper = Depends(get_media_data_wrapper)
    ):
        LOGGER.info('file: %r, input: %r', media.filename, media.media_type)
        return f'test: {media.filename}, {media.media_type}'

    @app.post("/process2")
    def process2(
        source: Annotated[
            ScienceBeamParserSessionSource,
            Depends(
                get_sciencebeam_parser_session_source_dependency_factory()
            )
        ]
    ):
        LOGGER.info('file: %r, input: %r', source.source_path, source.source_media_type)
        return f'test: {source.source_path}, {source.source_media_type}'

    return app
