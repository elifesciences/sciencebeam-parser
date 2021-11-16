import logging
from typing import Callable, Optional, Sequence, TypeVar

from flask import request
from werkzeug.exceptions import BadRequest

from sciencebeam_parser.utils.media_types import (
    get_first_matching_media_type
)
from sciencebeam_parser.utils.data_wrapper import MediaDataWrapper


LOGGER = logging.getLogger(__name__)


T = TypeVar('T')


DEFAULT_FILENAME = 'file'


def get_optional_post_data_wrapper() -> MediaDataWrapper:
    if not request.files:
        return MediaDataWrapper(
            data=request.data,
            media_type=request.mimetype,
            filename=request.args.get('filename')
        )
    supported_file_keys = ['file', 'input']
    for name in supported_file_keys:
        if name not in request.files:
            continue
        uploaded_file = request.files[name]
        data = uploaded_file.stream.read()
        return MediaDataWrapper(
            data=data,
            media_type=uploaded_file.mimetype,
            filename=uploaded_file.filename
        )
    raise BadRequest(
        f'missing file named one pf "{supported_file_keys}", found: {request.files.keys()}'
    )


def get_required_post_data_wrapper() -> MediaDataWrapper:
    data_wrapper = get_optional_post_data_wrapper()
    if not data_wrapper.data:
        raise BadRequest('no contents')
    return data_wrapper


def get_required_post_data() -> bytes:
    return get_required_post_data_wrapper().data


def get_request_accept_media_types() -> Sequence[str]:
    accept_media_types = list(request.accept_mimetypes.values())
    LOGGER.info('accept_media_types: %s', accept_media_types)
    return accept_media_types


def assert_and_get_first_matching_media_type(
    accept_media_types: Sequence[str],
    available_media_types: Sequence[str]
) -> str:
    media_type = get_first_matching_media_type(
        accept_media_types,
        available_media_types
    )
    if not media_type:
        raise BadRequest(
            f'unsupported accept media types: {accept_media_types},'
            f' supported types are: {available_media_types}'
        )
    LOGGER.info('resolved media type: %r', media_type)
    return media_type


def assert_and_get_first_accept_matching_media_type(
    available_media_types: Sequence[str]
) -> str:
    return assert_and_get_first_matching_media_type(
        get_request_accept_media_types(),
        available_media_types
    )


def get_typed_request_arg(
    name: str,
    type_: Callable[[str], T],
    default_value: Optional[T] = None,
    required: bool = False
) -> Optional[T]:
    value = request.args.get(name)
    if value:
        return type_(value)
    if required:
        raise ValueError(f'request arg {name} is required')
    return default_value


def str_to_bool(value: str) -> bool:
    value_lower = value.lower()
    if value_lower in {'true', '1'}:
        return True
    if value_lower in {'false', '0'}:
        return False
    raise ValueError('unrecognised boolean value: %r' % value)


def get_bool_request_arg(
    name: str,
    default_value: Optional[bool] = None,
    required: bool = False
) -> Optional[bool]:
    return get_typed_request_arg(
        name, str_to_bool, default_value=default_value, required=required
    )


def get_int_request_arg(
    name: str,
    default_value: Optional[int] = None,
    required: bool = False
) -> Optional[int]:
    return get_typed_request_arg(
        name, int, default_value=default_value, required=required
    )


def get_str_request_arg(
    name: str,
    default_value: Optional[str] = None,
    required: bool = False
) -> Optional[str]:
    return get_typed_request_arg(
        name, str, default_value=default_value, required=required
    )
