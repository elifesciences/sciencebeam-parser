import logging
from pathlib import Path

import pytest

from sciencebeam.utils.mime_type_constants import MimeTypes

from sciencebeam.pipeline_runners.direct_pipeline_runner import (
    main
)

from tests.utils.mock_server import MockServer


LOGGER = logging.getLogger(__name__)

PDF_CONTENT_1 = b'pdf content 1'
XML_CONTENT_1 = b'<article>xml content 1</article>'
XML_CONTENT_2 = b'<article>xml content 2</article>'


@pytest.mark.slow
class TestMainEndToEnd:
    def test_should_convert_single_file_using_file_list(
            self, temp_dir: Path, mock_server: MockServer):
        api_url = mock_server.add_response(
            '/api/convert', XML_CONTENT_1,
            mimetype=MimeTypes.JATS_XML,
            methods=('POST',)
        )
        LOGGER.debug('api_url: %s', api_url)
        source_path = temp_dir.joinpath('source')
        output_path = temp_dir.joinpath('output')
        source_path.mkdir(parents=True, exist_ok=True)
        source_path.joinpath('file1.pdf').write_bytes(PDF_CONTENT_1)
        source_path.joinpath('file-list.tsv').write_text('source_url\nfile1.pdf')
        output_file = output_path.joinpath('file1.xml')
        main([
            '--data-path=%s' % source_path,
            '--source-file-list=file-list.tsv',
            '--source-file-column=source_url',
            '--output-path=%s' % output_path,
            '--output-suffix=.xml',
            '--pipeline=api',
            '--api-url=%s' % api_url
        ])
        assert output_file.read_bytes() == XML_CONTENT_1

    def test_should_convert_single_file_using_file_path(
            self, temp_dir: Path, mock_server: MockServer):
        api_url = mock_server.add_response(
            '/api/convert', XML_CONTENT_1,
            mimetype=MimeTypes.JATS_XML,
            methods=('POST',)
        )
        LOGGER.debug('api_url: %s', api_url)
        source_path = temp_dir.joinpath('source')
        output_path = temp_dir.joinpath('output')
        source_path.mkdir(parents=True, exist_ok=True)
        source_path.joinpath('file1.pdf').write_bytes(PDF_CONTENT_1)
        output_file = output_path.joinpath('file1.xml')
        main([
            '--data-path=%s' % source_path,
            '--source-path=*.pdf',
            '--source-file-column=source_url',
            '--output-path=%s' % output_path,
            '--output-suffix=.xml',
            '--pipeline=api',
            '--api-url=%s' % api_url
        ])
        assert output_file.read_bytes() == XML_CONTENT_1

    def test_should_skip_existing_file(
            self, temp_dir: Path, mock_server: MockServer):
        api_url = mock_server.add_response(
            '/api/convert', XML_CONTENT_2,
            mimetype=MimeTypes.JATS_XML,
            methods=('POST',)
        )
        LOGGER.debug('api_url: %s', api_url)
        source_path = temp_dir.joinpath('source')
        output_path = temp_dir.joinpath('output')
        source_path.mkdir(parents=True, exist_ok=True)
        source_path.joinpath('file1.pdf').write_bytes(PDF_CONTENT_1)
        source_path.joinpath('file-list.tsv').write_text('source_url\nfile1.pdf')
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path.joinpath('file1.xml')
        output_file.write_bytes(XML_CONTENT_1)
        main([
            '--data-path=%s' % source_path,
            '--source-file-list=file-list.tsv',
            '--source-file-column=source_url',
            '--output-path=%s' % output_path,
            '--output-suffix=.xml',
            '--pipeline=api',
            '--api-url=%s' % api_url,
            '--resume'
        ])
        assert output_file.read_bytes() == XML_CONTENT_1
