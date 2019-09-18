import os
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


def _DocToTypeStep():
    return DocToTypeStep(output_ext=OUTPUT_EXT_1, output_mime_type=OUTPUT_MIME_TYPE_1)


class TestDocToTypeStep:
    def test_should_call_doc_to_type_and_return_pdf_content(self):
        assert _DocToTypeStep()(INPUT_DATA_1)['content'] == OUTPUT_CONTENT_1

    def test_should_call_doc_to_type_and_return_pdf_type(self):
        assert _DocToTypeStep()(INPUT_DATA_1)['type'] == OUTPUT_MIME_TYPE_1

    def test_should_call_doc_to_pdf_and_return_pdf_filename(self):
        assert _DocToTypeStep()(INPUT_DATA_1)['filename'] == OUTPUT_FILENAME_1

    def test_should_set_remove_line_no_to_true_if_request_args_is_y(self):
        assert _DocToTypeStep().get_doc_to_type_kwargs(
            INPUT_DATA_1, context={'request_args': {'remove_line_no': 'y'}}
        ).get('remove_line_no')

    def test_should_set_remove_line_no_to_false_if_request_args_is_n(self):
        assert not _DocToTypeStep().get_doc_to_type_kwargs(
            INPUT_DATA_1, context={'request_args': {'remove_line_no': 'n'}}
        ).get('remove_line_no')

    @patch.object(os, 'environ', {})
    def test_should_set_remove_line_no_to_true_if_env_var_is_y(self):
        os.environ['SCIENCEBEAM_REMOVE_LINE_NO'] = 'y'
        assert _DocToTypeStep().get_doc_to_type_kwargs(
            INPUT_DATA_1, context={}
        ).get('remove_line_no')

    @patch.object(os, 'environ', {})
    def test_should_set_remove_line_no_to_false_if_env_var_is_n(self):
        os.environ['SCIENCEBEAM_REMOVE_LINE_NO'] = 'n'
        assert not _DocToTypeStep().get_doc_to_type_kwargs(
            INPUT_DATA_1, context={}
        ).get('remove_line_no')

    @patch.object(os, 'environ', {})
    def test_should_prefer_request_args(self):
        os.environ['SCIENCEBEAM_REMOVE_LINE_NO'] = 'y'
        assert not _DocToTypeStep().get_doc_to_type_kwargs(
            INPUT_DATA_1, context={'request_args': {'remove_line_no': 'n'}}
        ).get('remove_line_no')
