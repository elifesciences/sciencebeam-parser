import logging
from typing import Sequence

from flask import request
from werkzeug.exceptions import BadRequest

from sciencebeam_parser.utils.media_types import get_first_matching_media_type


LOGGER = logging.getLogger(__name__)


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
