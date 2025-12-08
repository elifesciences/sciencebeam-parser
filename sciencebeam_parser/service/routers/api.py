import logging
from typing import Optional

from fastapi import (
    Body,
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    status
)


from sciencebeam_parser.app.parser import (
    ScienceBeamParser
)
from sciencebeam_parser.utils.data_wrapper import MediaDataWrapper
from sciencebeam_parser.utils.media_types import MediaTypes


LOGGER = logging.getLogger(__name__)


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


def create_api_app(
    sciencebeam_parser: ScienceBeamParser  # pylint: disable=unused-argument
) -> FastAPI:
    app = FastAPI()

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

    return app
