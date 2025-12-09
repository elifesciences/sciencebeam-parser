import logging
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI
)


from sciencebeam_parser.app.parser import (
    ScienceBeamParser,
    ScienceBeamParserSessionSource
)
from sciencebeam_parser.service.api.dependencies import (
    get_sciencebeam_parser_session_source_dependency_factory,
    resolve_media_data
)
from sciencebeam_parser.utils.data_wrapper import MediaDataWrapper


LOGGER = logging.getLogger(__name__)


def create_api_app(
    sciencebeam_parser: ScienceBeamParser
) -> FastAPI:
    app = FastAPI()
    app.state.sciencebeam_parser = sciencebeam_parser

    @app.get('/')
    def api_root() -> dict:
        return {
            'links': {}
        }

    @app.post("/process")
    def process(
        media: MediaDataWrapper = Depends(resolve_media_data)
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
