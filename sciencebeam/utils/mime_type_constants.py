import mimetypes


class MimeTypes:
    PDF = 'application/pdf'
    DOC = 'application/msword'
    DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    DOTX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.template'
    RTF = 'application/rtf'
    XML = 'application/xml'
    TEI_XML = 'application/tei+xml'
    JATS_XML = 'application/vnd.jats+xml'
    JSON = 'application/json'


# fixed mime type suffix map (which may be incorrectly defined in Python 3.5)
MIME_TYPE_SUFFIX_MAP = {
    MimeTypes.DOC: '.doc'
}


def guess_extension(mime_type: str) -> str:
    ext = MIME_TYPE_SUFFIX_MAP.get(mime_type)
    if not ext:
        ext = mimetypes.guess_extension(mime_type)
    return ext
