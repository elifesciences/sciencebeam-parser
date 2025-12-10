from sciencebeam_parser.utils.media_types import MediaTypes


TEI_XML_CONTENT_DOC = {
    "schema": {"type": "string", "format": "xml"},
    "example": "<TEI>...</TEI>"
}


JATS_XML_CONTENT_DOC = {
    "schema": {"type": "string", "format": "xml"},
    "example": "<article>...</article>"
}


TEI_ZIP_CONTENT_DOC = {
    "schema": {"type": "string", "format": "zip"},
}


JATS_ZIP_CONTENT_DOC = {
    "schema": {"type": "string", "format": "zip"},
}


PDF_CONTENT_DOC = {
    "schema": {"type": "string", "format": "pdf"},
}


TEI_AND_JATS_XML_CONTENT_DOC = {
    MediaTypes.TEI_XML: TEI_XML_CONTENT_DOC,
    MediaTypes.JATS_XML: JATS_XML_CONTENT_DOC
}

TEI_AND_JATS_ZIP_CONTENT_DOC = {
    MediaTypes.TEI_ZIP: TEI_XML_CONTENT_DOC,
    MediaTypes.JATS_ZIP: JATS_XML_CONTENT_DOC
}
