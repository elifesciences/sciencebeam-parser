from tempfile import TemporaryDirectory
from pathlib import Path

from flask import Blueprint, jsonify, request, Response, url_for
from werkzeug.exceptions import BadRequest

from pygrobid.external.pdfalto.wrapper import PdfAltoWrapper


def get_post_data():
    if not request.files:
        return request.data
    if 'file' not in request.files:
        raise BadRequest(
            'missing file named "file", found: %s ' % request.files.keys()
        )
    uploaded_file = request.files['file']
    return uploaded_file.read()


class ApiBlueprint(Blueprint):
    def __init__(self):
        super().__init__('api', __name__)
        self.route('/')(self.api_root)
        self.route("/pdfalto", methods=['POST'])(self.pdfalto)
        self.route("/pdfalto", methods=['GET'])(self.pdfalto_form)
        self.pdfalto_wrapper = PdfAltoWrapper.get()

    def api_root(self):
        return jsonify({
            'links': {
                'pdfalto': url_for('.pdfalto')
            }
        })

    def pdfalto(self):
        data = get_post_data()
        if not data:
            raise BadRequest('no contents')
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

    def pdfalto_form(self):
        return (
            '''
            <!doctype html>
            <title>PdfAlto convert PDF to LXML</title>
            <h1>PdfAlto convert PDF to LXML</h1>
            <form method=post enctype=multipart/form-data>
            <input type=file name=file>
            <input type=submit value=Upload>
            </form>
            '''
        )
