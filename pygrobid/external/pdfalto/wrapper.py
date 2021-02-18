import logging
import os
import sys

from subprocess import Popen, STDOUT


LOGGER = logging.getLogger(__name__)


def get_grobid_home_path() -> str:
    return os.environ.get('GROBID_HOME') or './grobid-home'


def get_pdfalto_binary_path() -> str:
    return get_grobid_home_path() + '/pdf2xml/lin-64/pdfalto'


class PdfAltoWrapper:
    def __init__(self, binary_path: str):
        self.binary_path = binary_path

    @staticmethod
    def get():
        return PdfAltoWrapper(get_pdfalto_binary_path())

    def get_command(self, pdf_path: str, output_path: str):
        return [
            self.binary_path,
            '-noImageInline',
            '-fullFontName',
            '-noLineNumbers',
            pdf_path,
            output_path
        ]

    def convert_pdf_to_pdfalto_xml(self, pdf_path: str, output_path: str):
        command = self.get_command(pdf_path, output_path)
        LOGGER.info('command: %s', command)
        LOGGER.info('command str: %s', ' '.join(command))
        with Popen(command, stdout=sys.stderr, stderr=STDOUT) as _:
            pass
