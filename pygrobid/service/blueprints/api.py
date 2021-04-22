import logging
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Optional

import yaml
from flask import Blueprint, jsonify, request, Response, url_for
from werkzeug.exceptions import BadRequest
from lxml import etree

from sciencebeam_trainer_delft.sequence_labelling.reader import load_data_crf_lines

from sciencebeam_trainer_delft.sequence_labelling.tag_formatter import (
    TagOutputFormats,
    iter_format_tag_result
)

from pygrobid.external.pdfalto.wrapper import PdfAltoWrapper
from pygrobid.models.model import Model
from pygrobid.models.segmentation.model import SegmentationModel
from pygrobid.models.header.model import HeaderModel
from pygrobid.document.tei_document import TeiDocument


LOGGER = logging.getLogger(__name__)


class RequestArgs:
    FIRST_PAGE = 'first_page'
    LAST_PAGE = 'last_page'
    OUTPUT_FORMAT = 'output_format'


class ModelOutputFormats:
    RAW_DATA = 'raw_data'


DEFAULT_MODEL_OUTPUT_FORMAT = TagOutputFormats.JSON
VALID_MODEL_OUTPUT_FORMATS = {
    ModelOutputFormats.RAW_DATA,
    TagOutputFormats.JSON,
    TagOutputFormats.DATA,
    TagOutputFormats.XML
}


def get_post_data():
    if not request.files:
        return request.data
    supported_file_keys = ['file', 'input']
    for name in supported_file_keys:
        if name not in request.files:
            continue
        uploaded_file = request.files[name]
        return uploaded_file.read()
    raise BadRequest(
        f'missing file named one pf "{supported_file_keys}", found: {request.files.keys()}'
    )


def get_required_post_data():
    data = get_post_data()
    if not data:
        raise BadRequest('no contents')
    return data


def get_int_request_arg(
    name: str,
    default_value: Optional[int] = None,
    required: bool = False
) -> Optional[int]:
    value = request.args.get(name)
    if value:
        return int(value)
    if required:
        raise ValueError(f'request arg {name} is required')
    return default_value


def _get_file_upload_form(title: str):
    return (
        '''
        <!doctype html>
        <title>{title}</title>
        <h1>{title}</h1>
        <form target=_blank method=post enctype=multipart/form-data>
        <input type=file name=file>
        <input type=submit value=Upload>
        </form>
        '''
    ).format(title=title)


class ModelNestedBluePrint:
    def __init__(
        self,
        name: str,
        model: Model,
        pdfalto_wrapper: PdfAltoWrapper
    ):
        self.name = name
        self.model = model
        self.pdfalto_wrapper = pdfalto_wrapper

    def add_routes(self, parent_blueprint: Blueprint, url_prefix: str):
        parent_blueprint.route(
            url_prefix, methods=['GET'], endpoint=f'{url_prefix}_get'
        )(self.handle_get)
        parent_blueprint.route(
            url_prefix, methods=['POST'], endpoint=f'{url_prefix}_post'
        )(self.handle_post)

    def handle_get(self):
        return _get_file_upload_form(f'{self.name} Model: convert PDF to data')

    def handle_post(self):  # pylint: disable=too-many-locals
        data = get_required_post_data()
        with TemporaryDirectory(suffix='-request') as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = temp_path / 'test.pdf'
            output_path = temp_path / 'test.lxml'
            first_page = get_int_request_arg(RequestArgs.FIRST_PAGE)
            last_page = get_int_request_arg(RequestArgs.LAST_PAGE)
            output_format = (
                request.args.get(RequestArgs.OUTPUT_FORMAT) or DEFAULT_MODEL_OUTPUT_FORMAT
            )
            assert output_format in VALID_MODEL_OUTPUT_FORMATS, \
                f'{output_format} not in {VALID_MODEL_OUTPUT_FORMATS}'
            pdf_path.write_bytes(data)
            self.pdfalto_wrapper.convert_pdf_to_pdfalto_xml(
                str(pdf_path),
                str(output_path),
                first_page=first_page,
                last_page=last_page
            )
            xml_content = output_path.read_bytes()
            root = etree.fromstring(xml_content)
            data_generator = self.model.get_data_generator()
            data_lines = data_generator.iter_data_lines_for_xml_root(root)
            response_type = 'text/plain'
            if output_format == ModelOutputFormats.RAW_DATA:
                response_content = '\n'.join(data_lines) + '\n'
            else:
                texts, features = load_data_crf_lines(data_lines)
                texts = texts.tolist()
                tag_result = self.model.predict_labels(
                    texts=texts, features=features, output_format=None
                )
                LOGGER.info('tag_result: %s', tag_result)
                formatted_tag_result_iterable = iter_format_tag_result(
                    tag_result,
                    output_format=output_format,
                    expected_tag_result=None,
                    texts=texts,
                    features=features,
                    model_name='header'
                )
                response_content = ''.join(formatted_tag_result_iterable)
                if output_format == TagOutputFormats.JSON:
                    response_type = 'application/json'
            LOGGER.debug('response_content: %r', response_content)
        headers = None
        return Response(response_content, headers=headers, mimetype=response_type)


class ApiBlueprint(Blueprint):
    def __init__(self):
        super().__init__('api', __name__)
        config = yaml.safe_load(Path('config.yml').read_text())
        LOGGER.info('config: %s', config)
        self.route('/')(self.api_root)
        self.route("/pdfalto", methods=['GET'])(self.pdfalto_form)
        self.route("/pdfalto", methods=['POST'])(self.pdfalto)
        self.route("/processFulltextDocument", methods=['GET'])(self.process_pdf_to_tei_form)
        self.route("/processFulltextDocument", methods=['POST'])(self.process_pdf_to_tei)
        self.pdfalto_wrapper = PdfAltoWrapper.get()
        self.segmentation_model = SegmentationModel(config['models']['segmentation']['path'])
        self.header_model = HeaderModel(config['models']['header']['path'])
        ModelNestedBluePrint(
            'Segmentation', model=self.segmentation_model, pdfalto_wrapper=self.pdfalto_wrapper
        ).add_routes(self, '/models/segmentation')
        ModelNestedBluePrint(
            'Header', model=self.header_model, pdfalto_wrapper=self.pdfalto_wrapper
        ).add_routes(self, '/models/header')

    def api_root(self):
        return jsonify({
            'links': {
                'pdfalto': url_for('.pdfalto')
            }
        })

    def pdfalto_form(self):
        return _get_file_upload_form('PdfAlto convert PDF to LXML')

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

    def process_pdf_to_tei_form(self):
        return _get_file_upload_form('Convert PDF to TEI')

    def process_pdf_to_tei(self):  # pylint: disable=too-many-locals
        data = get_required_post_data()
        with TemporaryDirectory(suffix='-request') as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = temp_path / 'test.pdf'
            output_path = temp_path / 'test.lxml'
            first_page = get_int_request_arg(RequestArgs.FIRST_PAGE)
            last_page = get_int_request_arg(RequestArgs.LAST_PAGE)
            pdf_path.write_bytes(data)
            self.pdfalto_wrapper.convert_pdf_to_pdfalto_xml(
                str(pdf_path),
                str(output_path),
                first_page=first_page,
                last_page=last_page
            )
            xml_content = output_path.read_bytes()
            root = etree.fromstring(xml_content)
            data_generator = self.header_model.get_data_generator()
            data_lines = data_generator.iter_data_lines_for_xml_root(root)
            texts, features = load_data_crf_lines(data_lines)
            texts = texts.tolist()
            tag_result = self.header_model.predict_labels(
                texts=texts, features=features, output_format=None
            )
            LOGGER.info('tag_result: %s', tag_result)
            entity_values = self.header_model.iter_entity_values_predicted_labels(tag_result[0])
            document = TeiDocument()
            self.header_model.update_document_with_entity_values(document, entity_values)
            response_type = 'application/xml'
            response_content = etree.tostring(document.root, pretty_print=True)
            LOGGER.debug('response_content: %r', response_content)
        headers = None
        return Response(response_content, headers=headers, mimetype=response_type)
