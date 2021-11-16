"""
Constants and functionality related to Media Types (formerly known as MIME types)

See:
  https://www.iana.org/assignments/media-types/media-types.xhtml
"""
import mimetypes
from typing import Optional, Sequence


class MediaTypes:
    """
    Media Types used by ScienceBeam Parser.
    Where possible, these correspond to official media types.
    In some instances, no official media type is defined yet.
    """
    PDF = 'application/pdf'
    DOC = 'application/msword'
    DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    DOTX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.template'
    RTF = 'application/rtf'
    XML = 'application/xml'
    ZIP = 'application/zip'
    TEI_XML = 'application/tei+xml'
    JATS_XML = 'application/vnd.jats+xml'
    TEI_ZIP = 'application/tei+xml+zip'
    JATS_ZIP = 'application/vnd.jats+xml+zip'
    ALTO_XML = 'application/vnd.alto+xml'
    JSON = 'application/json'
    OCTET_STREAM = 'application/octet-stream'


WILDCARD_MEDIA_TYPE = '*/*'


MEDIA_TYPE_SUFFIX_MAP = {
    # fixed mime type suffix map (which may be incorrectly defined in Python 3.5)
    MediaTypes.DOC: '.doc',
    # additional types
    MediaTypes.TEI_XML: '.tei.xml',
    MediaTypes.JATS_XML: '.jats.xml',
    MediaTypes.TEI_ZIP: '.tei.zip',
    MediaTypes.JATS_ZIP: '.jats.zip'
}


def guess_extension_for_media_type(media_type: str) -> Optional[str]:
    ext = MEDIA_TYPE_SUFFIX_MAP.get(media_type)
    if not ext:
        ext = mimetypes.guess_extension(media_type)
    return ext


def guess_media_type_for_filename(filename: str) -> Optional[str]:
    return mimetypes.guess_type(filename)[0]


def get_first_matching_media_type(
    accept_media_types: Sequence[str],
    available_media_types: Sequence[str]
) -> Optional[str]:
    if not available_media_types:
        return None
    if not accept_media_types:
        return available_media_types[0]
    for accept_media_type in accept_media_types:
        if accept_media_type == WILDCARD_MEDIA_TYPE:
            return available_media_types[0]
        for available_media_type in available_media_types:
            if accept_media_type == available_media_type:
                return available_media_type
    return None
