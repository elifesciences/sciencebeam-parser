import logging
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Iterable, Iterator, List, Type, TypeVar

from flask import Blueprint, jsonify, request, Response, url_for
from flask.helpers import send_file
from lxml import etree

from sciencebeam_trainer_delft.sequence_labelling.reader import load_data_crf_lines

from sciencebeam_trainer_delft.sequence_labelling.tag_formatter import (
    TagOutputFormats,
    iter_format_tag_result
)
from werkzeug.exceptions import BadRequest

from sciencebeam_parser.app.parser import (
    BadRequestScienceBeamParserError,
    ScienceBeamParser,
    ScienceBeamParserSession,
    ScienceBeamParserSessionSource
)
from sciencebeam_parser.external.pdfalto.wrapper import PdfAltoWrapper
from sciencebeam_parser.external.pdfalto.parser import parse_alto_root
from sciencebeam_parser.models.data import AppFeaturesContext, DocumentFeaturesContext
from sciencebeam_parser.models.model import Model
from sciencebeam_parser.document.layout_document import LayoutDocument
from sciencebeam_parser.document.semantic_document import (
    SemanticMixedContentWrapper,
    SemanticRawAffiliationAddress,
    SemanticRawAuthors,
    SemanticRawFigure,
    SemanticRawReference,
    SemanticRawReferenceText,
    SemanticRawTable,
    SemanticReference,
    T_SemanticContentWrapper,
    iter_by_semantic_type_recursively
)
from sciencebeam_parser.processors.fulltext.config import RequestFieldNames
from sciencebeam_parser.utils.data_wrapper import (
    get_data_wrapper_with_improved_media_type_or_filename
)
from sciencebeam_parser.utils.flask import (
    assert_and_get_first_accept_matching_media_type,
    get_bool_request_arg,
    get_int_request_arg,
    get_required_post_data,
    get_required_post_data_wrapper,
    get_str_request_arg
)
from sciencebeam_parser.utils.media_types import (
    MediaTypes
)
from sciencebeam_parser.utils.text import normalize_text, parse_comma_separated_value
from sciencebeam_parser.utils.tokenizer import get_tokenized_tokens
from sciencebeam_parser.processors.fulltext.api import (
    FullTextProcessorConfig
)


LOGGER = logging.getLogger(__name__)


T = TypeVar('T')


class RequestArgs:
    FIRST_PAGE = 'first_page'
    LAST_PAGE = 'last_page'
    OUTPUT_FORMAT = 'output_format'
    NO_USE_SEGMENTATION = 'no_use_segmentation'
    INCLUDES = 'includes'


class ModelOutputFormats:
    RAW_DATA = 'raw_data'


DEFAULT_MODEL_OUTPUT_FORMAT = TagOutputFormats.JSON
VALID_MODEL_OUTPUT_FORMATS = {
    ModelOutputFormats.RAW_DATA,
    TagOutputFormats.JSON,
    TagOutputFormats.DATA,
    TagOutputFormats.XML
}


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


def normalize_and_tokenize_text(text: str) -> List[str]:
    return get_tokenized_tokens(
        normalize_text(text),
        keep_whitespace=True
    )


def normalize_layout_document(
    layout_document: LayoutDocument,
    **kwargs
) -> LayoutDocument:
    return (
        layout_document
        .retokenize(tokenize_fn=normalize_and_tokenize_text)
        .remove_empty_blocks(**kwargs)
    )


class ModelNestedBluePrint:
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

    def add_routes(self, parent_blueprint: Blueprint, url_prefix: str):
        parent_blueprint.route(
            url_prefix, methods=['GET'], endpoint=f'{url_prefix}_get'
        )(self.handle_get)
        parent_blueprint.route(
            url_prefix, methods=['POST'], endpoint=f'{url_prefix}_post'
        )(self.handle_post)

    def handle_get(self):
        return _get_file_upload_form(f'{self.name} Model: convert PDF to data')

    def iter_filter_layout_document(
        self, layout_document: LayoutDocument
    ) -> Iterable[LayoutDocument]:
        return [layout_document]

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
        headers = None
        return Response(response_content, headers=headers, mimetype=response_type)


class SegmentedModelNestedBluePrint(ModelNestedBluePrint):
    def __init__(
        self,
        *args,
        segmentation_model: Model,
        segmentation_labels: List[str],
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.segmentation_model = segmentation_model
        self.segmentation_labels = segmentation_labels

    def iter_filter_layout_document_by_segmentation_labels(
        self,
        layout_document: LayoutDocument,
        segmentation_labels: List[str]
    ) -> Iterable[LayoutDocument]:
        assert self.segmentation_model is not None
        segmentation_label_result = (
            self.segmentation_model.get_label_layout_document_result(
                layout_document,
                app_features_context=self.app_features_context
            )
        )
        for segmentation_label in segmentation_labels:
            layout_document = segmentation_label_result.get_filtered_document_by_label(
                segmentation_label
            ).remove_empty_blocks()
            if not layout_document:
                LOGGER.info(
                    'empty document for segmentation label %r, available labels: %r',
                    segmentation_label,
                    segmentation_label_result.get_available_labels()
                )
                continue
            yield layout_document

    def filter_layout_document_by_segmentation_label(
        self,
        layout_document: LayoutDocument,
        segmentation_label: str
    ) -> LayoutDocument:
        for filtered_layout_document in self.iter_filter_layout_document_by_segmentation_labels(
            layout_document,
            segmentation_labels=[segmentation_label]
        ):
            return filtered_layout_document
        return LayoutDocument(pages=[])

    def iter_filter_layout_document(
        self, layout_document: LayoutDocument
    ) -> Iterable[LayoutDocument]:
        if get_bool_request_arg(RequestArgs.NO_USE_SEGMENTATION, default_value=False):
            return [layout_document]
        return self.iter_filter_layout_document_by_segmentation_labels(
            layout_document, segmentation_labels=self.segmentation_labels
        )


class NameHeaderModelNestedBluePrint(SegmentedModelNestedBluePrint):
    def __init__(
        self,
        *args,
        header_model: Model,
        merge_raw_authors: bool,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.header_model = header_model
        self.merge_raw_authors = merge_raw_authors

    def iter_filter_layout_document(
        self, layout_document: LayoutDocument
    ) -> Iterable[LayoutDocument]:
        header_layout_document = self.filter_layout_document_by_segmentation_label(
            layout_document, '<header>'
        )
        labeled_layout_tokens = self.header_model.predict_labels_for_layout_document(
            header_layout_document,
            app_features_context=self.app_features_context
        )
        LOGGER.debug('labeled_layout_tokens: %r', labeled_layout_tokens)
        semantic_raw_authors_list = list(
            SemanticMixedContentWrapper(list(
                self.header_model.iter_semantic_content_for_labeled_layout_tokens(
                    labeled_layout_tokens
                )
            )).iter_by_type(SemanticRawAuthors)
        )
        LOGGER.info('semantic_raw_authors_list count: %d', len(semantic_raw_authors_list))
        LOGGER.info('merge_raw_authors: %s', self.merge_raw_authors)
        if self.merge_raw_authors:
            return [
                LayoutDocument.for_blocks([
                    block
                    for semantic_raw_authors in semantic_raw_authors_list
                    for block in semantic_raw_authors.iter_blocks()
                ]).remove_empty_blocks()
            ]
        return [
            LayoutDocument.for_blocks(
                list(semantic_raw_authors.iter_blocks())
            ).remove_empty_blocks()
            for semantic_raw_authors in semantic_raw_authors_list
        ]


class AffiliationAddressModelNestedBluePrint(SegmentedModelNestedBluePrint):
    def __init__(self, *args, header_model: Model, **kwargs):
        super().__init__(*args, **kwargs)
        self.header_model = header_model

    def iter_filter_layout_document(
        self, layout_document: LayoutDocument
    ) -> Iterable[LayoutDocument]:
        header_layout_document = self.filter_layout_document_by_segmentation_label(
            layout_document, '<header>'
        )
        labeled_layout_tokens = self.header_model.predict_labels_for_layout_document(
            header_layout_document,
            app_features_context=self.app_features_context
        )
        LOGGER.debug('labeled_layout_tokens: %r', labeled_layout_tokens)
        semantic_raw_aff_address_list = list(
            SemanticMixedContentWrapper(list(
                self.header_model.iter_semantic_content_for_labeled_layout_tokens(
                    labeled_layout_tokens
                )
            )).iter_by_type(SemanticRawAffiliationAddress)
        )
        LOGGER.info('semantic_raw_aff_address_list count: %d', len(semantic_raw_aff_address_list))
        return [
            LayoutDocument.for_blocks(
                list(semantic_raw_aff_address.iter_blocks())
            ).remove_empty_blocks()
            for semantic_raw_aff_address in semantic_raw_aff_address_list
        ]


class CitationModelNestedBluePrint(SegmentedModelNestedBluePrint):
    def __init__(self, *args, reference_segmenter_model: Model, **kwargs):
        super().__init__(*args, **kwargs)
        self.reference_segmenter_model = reference_segmenter_model

    def iter_filter_layout_document(
        self, layout_document: LayoutDocument
    ) -> Iterable[LayoutDocument]:
        references_layout_document = self.filter_layout_document_by_segmentation_label(
            layout_document, '<references>'
        )
        labeled_layout_tokens = self.reference_segmenter_model.predict_labels_for_layout_document(
            references_layout_document,
            app_features_context=self.app_features_context
        )
        LOGGER.debug('labeled_layout_tokens: %r', labeled_layout_tokens)
        semantic_raw_references = list(
            SemanticMixedContentWrapper(list(
                self.reference_segmenter_model.iter_semantic_content_for_labeled_layout_tokens(
                    labeled_layout_tokens
                )
            )).iter_by_type(SemanticRawReference)
        )
        LOGGER.info('semantic_raw_references count: %d', len(semantic_raw_references))
        return [
            LayoutDocument.for_blocks(
                [semantic_raw_reference.view_by_type(SemanticRawReferenceText).merged_block]
            ).remove_empty_blocks()
            for semantic_raw_reference in semantic_raw_references
        ]


class NameCitationModelNestedBluePrint(SegmentedModelNestedBluePrint):
    def __init__(
        self,
        *args,
        reference_segmenter_model: Model,
        citation_model: Model,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.reference_segmenter_model = reference_segmenter_model
        self.citation_model = citation_model

    def iter_filter_layout_document(
        self, layout_document: LayoutDocument
    ) -> Iterable[LayoutDocument]:
        references_layout_document = self.filter_layout_document_by_segmentation_label(
            layout_document, '<references>'
        )
        labeled_layout_tokens = self.reference_segmenter_model.predict_labels_for_layout_document(
            references_layout_document,
            app_features_context=self.app_features_context
        )
        LOGGER.debug('labeled_layout_tokens: %r', labeled_layout_tokens)
        semantic_raw_references = list(
            SemanticMixedContentWrapper(list(
                self.reference_segmenter_model.iter_semantic_content_for_labeled_layout_tokens(
                    labeled_layout_tokens
                )
            )).iter_by_type(SemanticRawReference)
        )
        LOGGER.info('semantic_raw_references count: %d', len(semantic_raw_references))
        raw_reference_documents = [
            LayoutDocument.for_blocks(
                [semantic_raw_reference.view_by_type(SemanticRawReferenceText).merged_block]
            ).remove_empty_blocks()
            for semantic_raw_reference in semantic_raw_references
        ]
        citation_labeled_layout_tokens_list = (
            self.citation_model.predict_labels_for_layout_documents(
                raw_reference_documents,
                app_features_context=self.app_features_context
            )
        )
        raw_authors = [
            raw_author
            for citation_labeled_layout_tokens in citation_labeled_layout_tokens_list
            for ref in (
                self.citation_model.iter_semantic_content_for_labeled_layout_tokens(
                    citation_labeled_layout_tokens
                )
            )
            if isinstance(ref, SemanticReference)
            for raw_author in ref.iter_by_type(SemanticRawAuthors)
        ]
        return [
            LayoutDocument.for_blocks([raw_author.merged_block]).remove_empty_blocks()
            for raw_author in raw_authors
        ]


class FullTextChildModelNestedBluePrint(SegmentedModelNestedBluePrint):
    def __init__(
        self,
        *args,
        fulltext_model: Model,
        semantic_type: Type[T_SemanticContentWrapper],
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.fulltext_model = fulltext_model
        self.semantic_type = semantic_type

    def iter_filter_layout_document(
        self, layout_document: LayoutDocument
    ) -> Iterable[LayoutDocument]:
        fulltext_layout_documents = list(self.iter_filter_layout_document_by_segmentation_labels(
            layout_document, self.segmentation_labels
        ))
        fulltext_labeled_layout_tokens_list = (
            self.fulltext_model.predict_labels_for_layout_documents(
                fulltext_layout_documents,
                app_features_context=self.app_features_context
            )
        )
        LOGGER.debug('fulltext_labeled_layout_tokens_list: %r', fulltext_labeled_layout_tokens_list)
        semanti_content_list = [
            semantic_content
            for fulltext_labeled_layout_tokens in fulltext_labeled_layout_tokens_list
            for semantic_content in iter_by_semantic_type_recursively(
                self.fulltext_model.iter_semantic_content_for_labeled_layout_tokens(
                    fulltext_labeled_layout_tokens
                ),
                self.semantic_type
            )
        ]
        LOGGER.debug('semanti_content_list: %s', semanti_content_list)
        return [
            LayoutDocument.for_blocks([semanti_content.merged_block]).remove_empty_blocks()
            for semanti_content in semanti_content_list
        ]


class FigureModelNestedBluePrint(FullTextChildModelNestedBluePrint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, semantic_type=SemanticRawFigure, **kwargs)


class TableModelNestedBluePrint(FullTextChildModelNestedBluePrint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, semantic_type=SemanticRawTable, **kwargs)


class ApiBlueprint(Blueprint):
    def __init__(
        self,
        sciencebeam_parser: ScienceBeamParser
    ):
        super().__init__('api', __name__)
        LOGGER.debug('sciencebeam_parser: %r', sciencebeam_parser)
        self.sciencebeam_parser = sciencebeam_parser
        self.route('/')(self.api_root)
        self.route("/pdfalto", methods=['GET'])(self.pdfalto_form)
        self.route("/pdfalto", methods=['POST'])(self.pdfalto)
        self.route("/processHeaderDocument", methods=['GET'])(
            self.process_header_document_api_form
        )
        self.route("/processHeaderDocument", methods=['POST'])(
            self.process_header_document_api
        )
        self.route("/processFulltextDocument", methods=['GET'])(
            self.process_fulltext_document_api_form
        )
        self.route("/processFulltextDocument", methods=['POST'])(
            self.process_fulltext_document_api
        )
        self.route("/processReferences", methods=['GET'])(
            self.process_references_api_form
        )
        self.route("/processReferences", methods=['POST'])(
            self.process_references_api
        )
        self.route("/processFulltextAssetDocument", methods=['GET'])(
            self.process_pdf_to_tei_assets_zip_form
        )
        self.route("/processFulltextAssetDocument", methods=['POST'])(
            self.process_pdf_to_tei_assets_zip
        )
        self.route("/convert", methods=['GET'])(self.process_convert_api_form)
        self.route("/convert", methods=['POST'])(self.process_convert_api)
        self.pdfalto_wrapper = sciencebeam_parser.pdfalto_wrapper
        self.app_context = sciencebeam_parser.app_context
        self.fulltext_processor_config = sciencebeam_parser.fulltext_processor_config
        self.fulltext_models = sciencebeam_parser.fulltext_models
        self.app_features_context = sciencebeam_parser.app_features_context
        fulltext_models = self.fulltext_models
        app_features_context = self.app_features_context
        ModelNestedBluePrint(
            'Segmentation',
            model=fulltext_models.segmentation_model,
            pdfalto_wrapper=self.pdfalto_wrapper,
            app_features_context=app_features_context
        ).add_routes(self, '/models/segmentation')
        SegmentedModelNestedBluePrint(
            'Header',
            model=fulltext_models.header_model,
            pdfalto_wrapper=self.pdfalto_wrapper,
            app_features_context=app_features_context,
            segmentation_model=fulltext_models.segmentation_model,
            segmentation_labels=['<header>']
        ).add_routes(self, '/models/header')
        NameHeaderModelNestedBluePrint(
            'Name Header',
            model=fulltext_models.name_header_model,
            pdfalto_wrapper=self.pdfalto_wrapper,
            app_features_context=app_features_context,
            segmentation_model=fulltext_models.segmentation_model,
            segmentation_labels=['<header>'],
            header_model=fulltext_models.header_model,
            merge_raw_authors=self.fulltext_processor_config.merge_raw_authors
        ).add_routes(self, '/models/name-header')
        AffiliationAddressModelNestedBluePrint(
            'Affiliation Address',
            model=fulltext_models.affiliation_address_model,
            pdfalto_wrapper=self.pdfalto_wrapper,
            app_features_context=app_features_context,
            segmentation_model=fulltext_models.segmentation_model,
            segmentation_labels=['<header>'],
            header_model=fulltext_models.header_model
        ).add_routes(self, '/models/affiliation-address')
        fulltext_segmentation_labels = ['<body>', '<acknowledgement>', '<annex>']
        SegmentedModelNestedBluePrint(
            'FullText',
            model=fulltext_models.fulltext_model,
            pdfalto_wrapper=self.pdfalto_wrapper,
            app_features_context=app_features_context,
            segmentation_model=fulltext_models.segmentation_model,
            segmentation_labels=fulltext_segmentation_labels
        ).add_routes(self, '/models/fulltext')
        FigureModelNestedBluePrint(
            'Figure',
            model=fulltext_models.figure_model,
            pdfalto_wrapper=self.pdfalto_wrapper,
            app_features_context=app_features_context,
            segmentation_model=fulltext_models.segmentation_model,
            segmentation_labels=fulltext_segmentation_labels,
            fulltext_model=fulltext_models.fulltext_model
        ).add_routes(self, '/models/figure')
        TableModelNestedBluePrint(
            'Table',
            model=fulltext_models.table_model,
            pdfalto_wrapper=self.pdfalto_wrapper,
            app_features_context=app_features_context,
            segmentation_model=fulltext_models.segmentation_model,
            segmentation_labels=fulltext_segmentation_labels,
            fulltext_model=fulltext_models.fulltext_model
        ).add_routes(self, '/models/table')
        SegmentedModelNestedBluePrint(
            'Reference Segmenter',
            model=fulltext_models.reference_segmenter_model,
            pdfalto_wrapper=self.pdfalto_wrapper,
            app_features_context=app_features_context,
            segmentation_model=fulltext_models.segmentation_model,
            segmentation_labels=['<references>']
        ).add_routes(self, '/models/reference-segmenter')
        CitationModelNestedBluePrint(
            'Citation (Reference)',
            model=fulltext_models.citation_model,
            pdfalto_wrapper=self.pdfalto_wrapper,
            app_features_context=app_features_context,
            segmentation_model=fulltext_models.segmentation_model,
            segmentation_labels=['<references>'],
            reference_segmenter_model=fulltext_models.reference_segmenter_model
        ).add_routes(self, '/models/citation')
        NameCitationModelNestedBluePrint(
            'Name Citaton',
            model=fulltext_models.name_citation_model,
            pdfalto_wrapper=self.pdfalto_wrapper,
            app_features_context=app_features_context,
            segmentation_model=fulltext_models.segmentation_model,
            segmentation_labels=['<references>'],
            reference_segmenter_model=fulltext_models.reference_segmenter_model,
            citation_model=fulltext_models.citation_model
        ).add_routes(self, '/models/name-citation')

    def api_root(self):
        return jsonify({
            'links': {
                'pdfalto': url_for('.pdfalto')
            }
        })

    def pdfalto_form(self):
        return _get_file_upload_form('PdfAlto convert PDF to LXML')

    @contextmanager
    def _get_new_sciencebeam_parser_session(
        self, **kwargs
    ) -> Iterator[ScienceBeamParserSession]:
        with self.sciencebeam_parser.get_new_session(**kwargs) as session:
            first_page = get_int_request_arg(RequestArgs.FIRST_PAGE)
            last_page = get_int_request_arg(RequestArgs.LAST_PAGE)
            session.document_request_parameters.first_page = first_page
            session.document_request_parameters.last_page = last_page
            yield session

    @contextmanager
    def _get_new_sciencebeam_parser_source(
        self, **kwargs
    ) -> Iterator[ScienceBeamParserSessionSource]:
        data_wrapper = get_data_wrapper_with_improved_media_type_or_filename(
            get_required_post_data_wrapper()
        )
        with self._get_new_sciencebeam_parser_session(**kwargs) as session:
            source_path = session.temp_path / 'source.file'
            source_path.write_bytes(data_wrapper.data)
            yield session.get_source(
                source_path=str(source_path),
                source_media_type=data_wrapper.media_type
            )

    def pdfalto(self):
        response_type = 'text/xml'
        with self._get_new_sciencebeam_parser_source() as source:
            return send_file(
                source.get_local_file_for_response_media_type(
                    MediaTypes.ALTO_XML
                ),
                mimetype=response_type
            )

    def _process_pdf_to_response_media_type(
        self,
        response_media_type: str,
        fulltext_processor_config: FullTextProcessorConfig
    ):
        try:
            LOGGER.debug('creating session source')
            with self._get_new_sciencebeam_parser_source(
                fulltext_processor_config=fulltext_processor_config
            ) as source:
                LOGGER.debug('created session source: %r', source)
                actual_response_media_type = response_media_type
                if response_media_type in {
                    MediaTypes.TEI_XML, MediaTypes.JATS_XML
                }:
                    actual_response_media_type = MediaTypes.XML
                elif response_media_type in {
                    MediaTypes.TEI_ZIP, MediaTypes.JATS_ZIP
                }:
                    actual_response_media_type = MediaTypes.ZIP
                result_file = source.get_local_file_for_response_media_type(
                    response_media_type
                )
                LOGGER.debug('result_file: %r', result_file)
                assert isinstance(result_file, str)
                return send_file(
                    result_file,
                    mimetype=actual_response_media_type
                )
        except BadRequestScienceBeamParserError as exc:
            LOGGER.warning('bad request: %r', exc)
            return BadRequest(str(exc))

    def process_header_document_api_form(self):
        return _get_file_upload_form('Convert PDF to TEI (Header)')

    def process_header_document_api(self):
        response_media_type = assert_and_get_first_accept_matching_media_type(
            [MediaTypes.TEI_XML, MediaTypes.JATS_XML]
        )
        return self._process_pdf_to_response_media_type(
            response_media_type,
            fulltext_processor_config=self.fulltext_processor_config.get_for_header_document()
        )

    def process_fulltext_document_api_form(self):
        return _get_file_upload_form('Convert PDF to TEI (Full Text)')

    def process_fulltext_document_api(self):
        response_media_type = assert_and_get_first_accept_matching_media_type(
            [MediaTypes.TEI_XML, MediaTypes.JATS_XML]
        )
        return self._process_pdf_to_response_media_type(
            response_media_type,
            fulltext_processor_config=self.fulltext_processor_config
        )

    def process_references_api_form(self):
        return _get_file_upload_form('Convert PDF to TEI (References)')

    def process_references_api(self):
        response_media_type = assert_and_get_first_accept_matching_media_type(
            [MediaTypes.TEI_XML, MediaTypes.JATS_XML]
        )
        return self._process_pdf_to_response_media_type(
            response_media_type,
            fulltext_processor_config=self.fulltext_processor_config.get_for_requested_field_names({
                RequestFieldNames.REFERENCES
            })
        )

    def process_pdf_to_tei_assets_zip_form(self):
        return _get_file_upload_form('Convert PDF to TEI Assets ZIP')

    def process_pdf_to_tei_assets_zip(self):
        response_media_type = assert_and_get_first_accept_matching_media_type(
            [MediaTypes.TEI_ZIP, MediaTypes.JATS_ZIP]
        )
        return self._process_pdf_to_response_media_type(
            response_media_type,
            fulltext_processor_config=self.fulltext_processor_config
        )

    def process_convert_api_form(self):
        return _get_file_upload_form('Convert API')

    def process_convert_api(self):
        response_media_type = assert_and_get_first_accept_matching_media_type(
            [
                MediaTypes.JATS_XML, MediaTypes.TEI_XML,
                MediaTypes.JATS_ZIP, MediaTypes.TEI_ZIP,
                MediaTypes.PDF
            ]
        )
        includes_list = parse_comma_separated_value(
            get_str_request_arg(RequestArgs.INCLUDES) or ''
        )
        LOGGER.info('includes_list: %r', includes_list)
        fulltext_processor_config = self.fulltext_processor_config.get_for_requested_field_names(
            set(includes_list)
        )
        LOGGER.info('fulltext_processor_config: %r', fulltext_processor_config)
        return self._process_pdf_to_response_media_type(
            response_media_type,
            fulltext_processor_config=fulltext_processor_config
        )
