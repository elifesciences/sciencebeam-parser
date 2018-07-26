from mock import patch

import pytest

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import doc_to_docx_pipeline as doc_to_docx_pipeline_module
from .doc_to_docx_pipeline import (
  DocToDocxStep,
  DocToDocxPipeline
)

DOC_CONTENT_1 = b'doc content 1'
DOC_FILENAME_1 = 'test1.doc'

DOCX_CONTENT_1 = b'docx content 1'
DOCX_FILENAME_1 = 'test1.docx'

DOC_DATA_1 = {
  'filename': DOC_FILENAME_1,
  'content': DOC_CONTENT_1,
  'type': MimeTypes.DOC
}

@pytest.fixture(name='doc_to_docx_mock', autouse=True)
def _mock_doc_to_docx():
  with patch.object(doc_to_docx_pipeline_module, 'doc_to_docx') as m:
    m.return_value = DOCX_CONTENT_1
    yield m

class TestDocToPdfStep(object):
  def test_should_call_doc_to_pdf_and_return_pdf_content(self):
    assert DocToDocxStep()(DOC_DATA_1)['content'] == DOCX_CONTENT_1

  def test_should_call_doc_to_pdf_and_return_pdf_type(self):
    assert DocToDocxStep()(DOC_DATA_1)['type'] == MimeTypes.DOCX

  def test_should_call_doc_to_pdf_and_return_pdf_filename(self):
    assert DocToDocxStep()(DOC_DATA_1)['filename'] == DOCX_FILENAME_1
