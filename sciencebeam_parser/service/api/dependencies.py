import logging
from typing import Annotated, Iterator, Optional, Protocol

from fastapi import (
    Depends,
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


async def get_media_data_wrapper(
    request: Request,
    input: Annotated[Optional[UploadFile], File()] = None,  # pylint: disable=redefined-builtin
    filename: Optional[str] = None,
) -> MediaDataWrapper:
    """
    Prefer the documented `input` param, but also accept:
    - legacy 'file' field in multipart form
    - raw request body
    """
    if input is not None:
        return get_media_data_wrapper_for_upload_file(input)

    form = await request.form()
    file = form.get('file')
    if isinstance(input, UploadFile):
        return get_media_data_wrapper_for_upload_file(file)

    body = await request.body()
    if body:
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
        sciencebeam_parser: Annotated[ScienceBeamParser, Depends(get_sciencebeam_parser)],
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> Iterator[ScienceBeamParserSession]:
        with sciencebeam_parser.get_new_session(**session_kwargs) as session:
            session.document_request_parameters.first_page = first_page
            session.document_request_parameters.last_page = last_page
            yield session

    return get_session


def get_sciencebeam_parser_session_source_dependency_factory(
    **session_kwargs,
) -> ScienceBeamParserSessionSourceDependencyFactory:
    def get_source(
        *,
        session: Annotated[
            ScienceBeamParserSession,
            Depends(
                get_sciencebeam_parser_session_dependency_factory(**session_kwargs)
            )
        ],
        data_wrapper: Annotated[MediaDataWrapper, Depends(get_media_data_wrapper)],
    ) -> Iterator[ScienceBeamParserSessionSource]:
        source_path = session.temp_path / "source.file"
        source_path.write_bytes(data_wrapper.data)

        yield session.get_source(
            source_path=str(source_path),
            source_media_type=data_wrapper.media_type,
        )

    return get_source
