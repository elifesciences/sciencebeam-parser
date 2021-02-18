from pathlib import Path

import pytest

from pygrobid.external.pdfalto.wrapper import (
    PdfAltoWrapper
)


EXAMPLE_PDF_PATH = 'test-data/minimal-example.pdf'


@pytest.fixture(name='pdfalto_wrapper', scope='session')
def _pdfalto_wrapper() -> PdfAltoWrapper:
    return PdfAltoWrapper.get()


class TestPdfAltoWrapper:
    def test_should_convert_example_document(
        self,
        pdfalto_wrapper: PdfAltoWrapper,
        tmp_path: Path
    ):
        output_path = tmp_path / 'test.lxml'
        pdfalto_wrapper.convert_pdf_to_pdfalto_xml(
            EXAMPLE_PDF_PATH,
            str(output_path)
        )
        assert output_path.exists()
