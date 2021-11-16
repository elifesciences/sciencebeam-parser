from typing import NamedTuple, Optional


from sciencebeam_parser.utils.media_types import (
    MediaTypes,
    guess_extension_for_media_type,
    guess_media_type_for_filename
)


DEFAULT_FILENAME = 'file'


class MediaDataWrapper(NamedTuple):
    data: bytes
    media_type: str
    filename: Optional[str] = None


def get_data_wrapper_with_improved_media_type_or_filename(
    data_wrapper: MediaDataWrapper
) -> MediaDataWrapper:
    if not data_wrapper.filename:
        return data_wrapper._replace(filename='%s%s' % (
            DEFAULT_FILENAME, guess_extension_for_media_type(data_wrapper.media_type) or ''
        ))
    if not data_wrapper.media_type or data_wrapper.media_type == MediaTypes.OCTET_STREAM:
        media_type = guess_media_type_for_filename(data_wrapper.filename)
        if media_type:
            return data_wrapper._replace(media_type=media_type)
    return data_wrapper
