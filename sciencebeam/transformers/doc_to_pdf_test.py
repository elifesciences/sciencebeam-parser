import os
from mock import patch

import pytest

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import doc_to_pdf as doc_to_pdf_module
from .doc_to_pdf import doc_to_pdf

DOC_CONTENT_1 = b'doc content 1'
PDF_CONTENT_1 = b'pdf content 1'

@pytest.fixture(name='check_output_mock', autouse=True)
def _mock_check_output():
  with patch.object(doc_to_pdf_module, 'check_output') as m:
    yield m

@pytest.fixture(name='TemporaryDirectory_mock', autouse=True)
def _mock_temp_directory(tmpdir):
  with patch.object(doc_to_pdf_module, 'TemporaryDirectory') as m:
    m.return_value.__enter__.return_value = str(tmpdir)
    yield m

class TestDocToPdf(object):
  def test_should_return_pdf(self, tmpdir):
    tmpdir.join('temp.pdf').write(PDF_CONTENT_1)
    assert doc_to_pdf(DOC_CONTENT_1, MimeTypes.DOC) == PDF_CONTENT_1

  def test_should_call_check_output_with_doc(self, tmpdir, check_output_mock):
    tmpdir.join('temp.pdf').write(PDF_CONTENT_1)
    doc_to_pdf(DOC_CONTENT_1, MimeTypes.DOC)
    check_output_mock.assert_called_with([
      'lowriter', '--convert-to', 'pdf', '--outdir', str(tmpdir),
      os.path.join(str(tmpdir), 'temp.doc')
    ])

  def test_should_call_check_output_with_docx(self, tmpdir, check_output_mock):
    tmpdir.join('temp.pdf').write(PDF_CONTENT_1)
    doc_to_pdf(DOC_CONTENT_1, MimeTypes.DOCX)
    check_output_mock.assert_called()
    assert check_output_mock.call_args[0][0][-1] == os.path.join(str(tmpdir), 'temp.docx')

  def test_should_call_check_output_with_dotx(self, tmpdir, check_output_mock):
    tmpdir.join('temp.pdf').write(PDF_CONTENT_1)
    doc_to_pdf(DOC_CONTENT_1, MimeTypes.DOTX)
    check_output_mock.assert_called()
    assert check_output_mock.call_args[0][0][-1] == os.path.join(str(tmpdir), 'temp.dotx')

  def test_should_call_check_output_with_rtf(self, tmpdir, check_output_mock):
    tmpdir.join('temp.pdf').write(PDF_CONTENT_1)
    doc_to_pdf(DOC_CONTENT_1, MimeTypes.RTF)
    check_output_mock.assert_called()
    assert check_output_mock.call_args[0][0][-1] == os.path.join(str(tmpdir), 'temp.rtf')
