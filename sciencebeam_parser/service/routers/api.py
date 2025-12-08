import logging

from fastapi import FastAPI


from sciencebeam_parser.app.parser import (
    ScienceBeamParser
)


LOGGER = logging.getLogger(__name__)


def create_api_app(
    sciencebeam_parser: ScienceBeamParser  # pylint: disable=unused-argument
) -> FastAPI:
    app = FastAPI()

    @app.get('/')
    def api_root() -> dict:
        return {
            'links': {}
        }

    return app
