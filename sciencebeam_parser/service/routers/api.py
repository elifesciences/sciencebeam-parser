import logging
from typing import Annotated, Iterator, Optional, Protocol

from fastapi import (
    Body,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
    status
)


from sciencebeam_parser.app.parser import (
    ScienceBeamParser,
    ScienceBeamParserSession,
    ScienceBeamParserSessionSource
)
from sciencebeam_parser.utils.data_wrapper import MediaDataWrapper
from sciencebeam_parser.utils.media_types import MediaTypes


LOGGER = logging.getLogger(__name__)


class ScienceBeamParserSessionDependencyFactory(Protocol):
    def __call__(self, *args, **kwargs) -> Iterator[ScienceBeamParserSession]:
        pass


class ScienceBeamParserSessionSourceDependencyFactory(Protocol):
    def __call__(self, *args, **kwargs) -> Iterator[ScienceBeamParserSessionSource]:
        pass


def get_media_data_wrapper_for_upload_file(
    upload_file: UploadFile,
    filename: Optional[str] = None
) -> MediaDataWrapper:
    data = upload_file.file.read()
    return MediaDataWrapper(
        data=data,
        media_type=upload_file.content_type or MediaTypes.OCTET_STREAM,
        filename=upload_file.filename or filename,
    )


def resolve_media_data(
    file: Optional[UploadFile] = File(None),
    input: Optional[UploadFile] = File(None),  # pylint: disable=redefined-builtin
    body: Optional[bytes] = Body(None),
    filename: Optional[str] = None,
) -> MediaDataWrapper:
    provided = [x for x in (file, input, body) if x is not None]
    if len(provided) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="provide exactly one of 'file', 'input' or raw body",
        )
    if file is not None:
        return get_media_data_wrapper_for_upload_file(file)
    if input is not None:
        return get_media_data_wrapper_for_upload_file(input)
    if body is not None:
        return MediaDataWrapper(
            data=body,
            media_type=MediaTypes.OCTET_STREAM,
            filename=filename,
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="one of 'file', 'input' or raw body is required",
    )


def get_sciencebeam_parser(request: Request) -> ScienceBeamParser:
    return request.app.state.sciencebeam_parser


def get_sciencebeam_parser_session_dependency_factory(
    **session_kwargs,
) -> ScienceBeamParserSessionDependencyFactory:
    def get_session(
        *,
        sciencebeam_parser: ScienceBeamParser = Depends(get_sciencebeam_parser)
    ) -> Iterator[ScienceBeamParserSession]:
        with sciencebeam_parser.get_new_session(**session_kwargs) as session:
            yield session

    return get_session


def get_sciencebeam_parser_session_source_dependency_factory(
    **session_kwargs,
) -> ScienceBeamParserSessionSourceDependencyFactory:
    def get_source(
        *,
        session: ScienceBeamParserSession = Depends(
            get_sciencebeam_parser_session_dependency_factory(**session_kwargs)
        ),
        data_wrapper: MediaDataWrapper = Depends(resolve_media_data),
    ) -> Iterator[ScienceBeamParserSessionSource]:
        source_path = session.temp_path / "source.file"
        source_path.write_bytes(data_wrapper.data)

        yield session.get_source(
            source_path=str(source_path),
            source_media_type=data_wrapper.media_type,
        )

    return get_source


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
