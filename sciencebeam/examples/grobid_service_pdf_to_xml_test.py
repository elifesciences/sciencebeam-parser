import logging
from mock import patch, DEFAULT

import pytest

import apache_beam as beam

from sciencebeam_utils.beam_utils.testing import (
    BeamTest,
    TestPipeline
)

import sciencebeam.examples.grobid_service_pdf_to_xml as pipeline_module
from sciencebeam.examples.grobid_service_pdf_to_xml import (
    configure_pipeline,
    parse_args
)


PDF_PATH = '*/*.pdf'
PDF_FILE_1 = '1/file1.pdf'

PDF_CONTENT_1 = b'pdf content'
TEI_XML_CONTENT_1 = b'<TEI>tei content</TEI>'


MIN_ARGV = [
    '--input=' + PDF_PATH
]


def setup_module():
    logging.basicConfig(level='DEBUG')


def get_default_args():
    return parse_args(MIN_ARGV)


def fake_pdf_png_page(i=0):
    return 'fake pdf png page: %d' % i


def patch_pipeline_module(**kwargs):
    always_mock = {
        'ReadFileNamesAndContent',
        'grobid_service',
        'WriteToFile'
    }

    return patch.multiple(
        pipeline_module,
        **{
            k: kwargs.get(k, DEFAULT)
            for k in always_mock
        }
    )


@pytest.mark.slow
class TestConfigurePipeline(BeamTest):
    def test_should_pass_input_pattern_to_read_file_names_and_content(self):
        with patch_pipeline_module() as mocks:
            opt = get_default_args()
            with TestPipeline() as p:
                mocks['ReadFileNamesAndContent'].return_value = beam.Create([
                    (PDF_FILE_1, PDF_CONTENT_1)
                ])
                mocks['grobid_service'].return_value = lambda x: (
                    PDF_FILE_1, TEI_XML_CONTENT_1
                )
                mocks['WriteToFile'].return_value = beam.Map(lambda x: x)
                configure_pipeline(p, opt)

            mocks['ReadFileNamesAndContent'].assert_called_with(
                opt.input
            )
