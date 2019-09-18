from mock import patch

import pytest

from sciencebeam.pipelines import doc_to_type_pipeline as doc_to_type_pipeline_module
from sciencebeam.pipelines.doc_to_type_pipeline import (
    DocToTypeStep
)


INPUT_CONTENT_1 = b'input content 1'
INPUT_FILENAME_1 = 'test1.in1'
INPUT_MIME_TYPE_1 = 'in/mime1'

OUTPUT_EXT_1 = '.ext1'
OUTPUT_MIME_TYPE_1 = 'out/mime1'
OUTPUT_CONTENT_1 = b'output content 1'
OUTPUT_FILENAME_1 = 'test1' + OUTPUT_EXT_1

INPUT_DATA_1 = {
    'filename': INPUT_FILENAME_1,
    'content': INPUT_CONTENT_1,
    'type': INPUT_MIME_TYPE_1
}


@pytest.fixture(name='doc_to_type_mock', autouse=True)
def _mock_doc_to_docx():
    with patch.object(doc_to_type_pipeline_module, 'doc_to_type') as m:
        m.return_value = OUTPUT_CONTENT_1
        yield m


def _DocToXyzStep():
    return DocToTypeStep(output_ext=OUTPUT_EXT_1, output_mime_type=OUTPUT_MIME_TYPE_1)


class TestDocToXyzStep:
    def test_should_call_doc_to_type_and_return_pdf_content(self):
        assert _DocToXyzStep()(INPUT_DATA_1)['content'] == OUTPUT_CONTENT_1

    def test_should_call_doc_to_type_and_return_pdf_type(self):
        assert _DocToXyzStep()(INPUT_DATA_1)['type'] == OUTPUT_MIME_TYPE_1

    def test_should_call_doc_to_pdf_and_return_pdf_filename(self):
        assert _DocToXyzStep()(INPUT_DATA_1)['filename'] == OUTPUT_FILENAME_1
