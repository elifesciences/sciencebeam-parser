from mock import patch

import pytest

from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam.pipelines import doc_to_pdf_pipeline as doc_to_pdf_pipeline_module
from sciencebeam.pipelines.doc_to_pdf_pipeline import (
    DocToPdfStep
)

DOC_CONTENT_1 = b'doc content 1'
DOC_FILENAME_1 = 'test1.doc'

PDF_CONTENT_1 = b'pdf content 1'
PDF_FILENAME_1 = 'test1.pdf'

DOC_DATA_1 = {
    'filename': DOC_FILENAME_1,
    'content': DOC_CONTENT_1,
    'type': MimeTypes.DOC
}


@pytest.fixture(name='doc_to_pdf_mock', autouse=True)
def _mock_doc_to_pdf():
    with patch.object(doc_to_pdf_pipeline_module, 'doc_to_pdf') as m:
        m.return_value = PDF_CONTENT_1
        yield m


class TestDocToPdfStep(object):
    def test_should_call_doc_to_pdf_and_return_pdf_content(self):
        assert DocToPdfStep()(DOC_DATA_1)['content'] == PDF_CONTENT_1

    def test_should_call_doc_to_pdf_and_return_pdf_type(self):
        assert DocToPdfStep()(DOC_DATA_1)['type'] == MimeTypes.PDF

    def test_should_call_doc_to_pdf_and_return_pdf_filename(self):
        assert DocToPdfStep()(DOC_DATA_1)['filename'] == PDF_FILENAME_1
