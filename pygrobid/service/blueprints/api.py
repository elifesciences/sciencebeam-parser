import logging
from tempfile import TemporaryDirectory
from pathlib import Path

from flask import Blueprint, jsonify, request, Response, url_for
from werkzeug.exceptions import BadRequest
from lxml import etree

from pygrobid.external.pdfalto.wrapper import PdfAltoWrapper
from pygrobid.models.header.data import HeaderDataGenerator


LOGGER = logging.getLogger(__name__)


def get_post_data():
    if not request.files:
        return request.data
    if 'file' not in request.files:
        raise BadRequest(
            'missing file named "file", found: %s ' % request.files.keys()
        )
    uploaded_file = request.files['file']
    return uploaded_file.read()


def get_required_post_data():
    data = get_post_data()
    if not data:
        raise BadRequest('no contents')
    return data


class ApiBlueprint(Blueprint):
    def __init__(self):
        super().__init__('api', __name__)
        self.route('/')(self.api_root)
        self.route("/pdfalto", methods=['GET'])(self.pdfalto_form)
        self.route("/pdfalto", methods=['POST'])(self.pdfalto)
        self.route("/models/header", methods=['GET'])(self.models_header_form)
        self.route("/models/header", methods=['POST'])(self.models_header)
        self.pdfalto_wrapper = PdfAltoWrapper.get()

    def api_root(self):
        return jsonify({
            'links': {
                'pdfalto': url_for('.pdfalto')
            }
        })

    def _get_form(self, title: str):
        return (
            '''
            <!doctype html>
            <title>{title}</title>
            <h1>{title}</h1>
            <form method=post enctype=multipart/form-data>
            <input type=file name=file>
            <input type=submit value=Upload>
            </form>
            '''
        ).format(title=title)

    def pdfalto_form(self):
        return self._get_form('PdfAlto convert PDF to LXML')

    def pdfalto(self):
        data = get_required_post_data()
        with TemporaryDirectory(suffix='-request') as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = temp_path / 'test.pdf'
            output_path = temp_path / 'test.lxml'
            pdf_path.write_bytes(data)
            self.pdfalto_wrapper.convert_pdf_to_pdfalto_xml(
                str(pdf_path),
                str(output_path)
            )
            response_content = output_path.read_text()
        response_type = 'text/xml'
        headers = None
        return Response(response_content, headers=headers, mimetype=response_type)

    def models_header_form(self):
        return self._get_form('Header Model: convert PDF to data')

    def models_header(self):
        data = get_required_post_data()
        with TemporaryDirectory(suffix='-request') as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = temp_path / 'test.pdf'
            output_path = temp_path / 'test.lxml'
            pdf_path.write_bytes(data)
            self.pdfalto_wrapper.convert_pdf_to_pdfalto_xml(
                str(pdf_path),
                str(output_path)
            )
            xml_content = output_path.read_bytes()
            root = etree.fromstring(xml_content)
            response_content = '\n'.join(
                HeaderDataGenerator().iter_data_lines_for_xml_root(root)
            )
            LOGGER.debug('response_content: %r', response_content)
        response_type = 'text/plain'
        headers = None
        return Response(response_content, headers=headers, mimetype=response_type)
