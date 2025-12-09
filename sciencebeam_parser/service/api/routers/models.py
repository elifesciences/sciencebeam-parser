import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Iterable

from lxml import etree

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import FileResponse

from sciencebeam_trainer_delft.sequence_labelling.reader import load_data_crf_lines
from sciencebeam_trainer_delft.sequence_labelling.tag_formatter import (
    TagOutputFormats,
    iter_format_tag_result
)

from sciencebeam_parser.app.parser import (
    ScienceBeamParser,
    ScienceBeamParserSessionSource,
    normalize_layout_document
)
from sciencebeam_parser.document.layout_document import LayoutDocument
from sciencebeam_parser.external.pdfalto.parser import parse_alto_root
from sciencebeam_parser.external.pdfalto.wrapper import PdfAltoWrapper
from sciencebeam_parser.models.data import AppFeaturesContext, DocumentFeaturesContext
from sciencebeam_parser.models.model import Model
from sciencebeam_parser.service.api.dependencies import (
    get_sciencebeam_parser_session_source_dependency_factory
)


LOGGER = logging.getLogger(__name__)


class ModelOutputFormats:
    RAW_DATA = 'raw_data'


DEFAULT_MODEL_OUTPUT_FORMAT = TagOutputFormats.JSON

VALID_MODEL_OUTPUT_FORMATS = [
    TagOutputFormats.JSON,
    ModelOutputFormats.RAW_DATA,
    TagOutputFormats.DATA,
    TagOutputFormats.XML
]


class ModelResponseRouterFactory:
    def __init__(
        self,
        name: str,
        model: Model,
        pdfalto_wrapper: PdfAltoWrapper,
        app_features_context: AppFeaturesContext,
        model_name: str = 'dummy'
    ):
        self.name = name
        self.model = model
        self.pdfalto_wrapper = pdfalto_wrapper
        self.app_features_context = app_features_context
        self.model_name = model_name

    def create_router(self) -> APIRouter:
        router = APIRouter()

        @router.post('', description=self.model_name)
        def process_post(
            source: Annotated[
                ScienceBeamParserSessionSource,
                Depends(
                    get_sciencebeam_parser_session_source_dependency_factory()
                )
            ],
            output_format: Annotated[
                str,
                Query(json_schema_extra={
                    'enum': VALID_MODEL_OUTPUT_FORMATS
                })
            ] = DEFAULT_MODEL_OUTPUT_FORMAT,
        ) -> FileResponse:
            LOGGER.info('model_name: %r', self.model_name)
            return self.handle_post(
                source=source,
                output_format=output_format
            )
        return router

    def iter_filter_layout_document(
        self, layout_document: LayoutDocument
    ) -> Iterable[LayoutDocument]:
        return [layout_document]

    def handle_post(  # pylint: disable=too-many-locals
        self,
        source: ScienceBeamParserSessionSource,
        output_format: str
    ):
        with TemporaryDirectory(suffix='-request') as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = source.source_path
            output_path = temp_path / 'test.lxml'
            first_page = source.document_request_parameters.first_page
            last_page = source.document_request_parameters.last_page
            assert output_format in VALID_MODEL_OUTPUT_FORMATS, \
                f'{output_format} not in {VALID_MODEL_OUTPUT_FORMATS}'
            self.pdfalto_wrapper.convert_pdf_to_pdfalto_xml(
                str(pdf_path),
                str(output_path),
                first_page=first_page,
                last_page=last_page
            )
            xml_content = output_path.read_bytes()
            root = etree.fromstring(xml_content)
            layout_document_iterable = self.iter_filter_layout_document(
                normalize_layout_document(
                    parse_alto_root(root)
                )
            )
            data_generator = self.model.get_data_generator(
                DocumentFeaturesContext(
                    app_features_context=self.app_features_context
                )
            )
            data_lines = data_generator.iter_data_lines_for_layout_documents(
                layout_document_iterable
            )
            response_type = 'text/plain'
            if output_format == ModelOutputFormats.RAW_DATA:
                response_content = '\n'.join(data_lines) + '\n'
            else:
                texts, features = load_data_crf_lines(data_lines)
                LOGGER.info('texts length: %d', len(texts))
                if not len(texts):  # pylint: disable=len-as-condition
                    tag_result = []
                else:
                    texts = texts.tolist()
                    tag_result = self.model.predict_labels(
                        texts=texts, features=features, output_format=None
                    )
                LOGGER.debug('tag_result: %s', tag_result)
                formatted_tag_result_iterable = iter_format_tag_result(
                    tag_result,
                    output_format=output_format,
                    expected_tag_result=None,
                    texts=texts,
                    features=features,
                    model_name=self.model_name
                )
                response_content = ''.join(formatted_tag_result_iterable)
                if output_format == TagOutputFormats.JSON:
                    response_type = 'application/json'
            LOGGER.debug('response_content: %r', response_content)
        return Response(
            content=response_content,
            media_type=response_type
        )


def create_models_router(
    sciencebeam_parser: ScienceBeamParser
) -> APIRouter:
    router = APIRouter(tags=['models'])

    pdfalto_wrapper = sciencebeam_parser.pdfalto_wrapper
    fulltext_models = sciencebeam_parser.fulltext_models
    app_features_context = sciencebeam_parser.app_features_context

    router.include_router(ModelResponseRouterFactory(
        'Segmentation',
        model=fulltext_models.segmentation_model,
        pdfalto_wrapper=pdfalto_wrapper,
        app_features_context=app_features_context
    ).create_router(), prefix='/models/segmentation')

    return router
