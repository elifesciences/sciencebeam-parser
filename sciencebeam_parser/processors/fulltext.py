import logging
from dataclasses import dataclass
from typing import (
    Iterable,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union
)

from sciencebeam_parser.app.context import AppContext
from sciencebeam_parser.config.config import AppConfig
from sciencebeam_parser.models.data import AppFeaturesContext, DEFAULT_APP_FEATURES_CONTEXT
from sciencebeam_parser.models.model import LayoutDocumentLabelResult, Model
from sciencebeam_parser.models.model_impl_factory import get_model_impl_factory_for_config
from sciencebeam_parser.utils.misc import iter_ids

from sciencebeam_parser.document.semantic_document import (
    SemanticAffiliationAddress,
    SemanticAuthor,
    SemanticCitation,
    SemanticContentWrapper,
    SemanticDocument,
    SemanticEditor,
    SemanticFigure,
    SemanticFigureCitation,
    SemanticInvalidReference,
    SemanticLabel,
    SemanticMixedContentWrapper,
    SemanticRawAffiliationAddress,
    SemanticRawAuthors,
    SemanticRawEditors,
    SemanticRawFigure,
    SemanticRawReference,
    SemanticRawReferenceText,
    SemanticRawTable,
    SemanticReference,
    SemanticReferenceCitation,
    SemanticReferenceList,
    SemanticSection,
    SemanticSectionTypes,
    SemanticTable,
    SemanticTableCitation,
    T_SemanticContentWrapper,
    T_SemanticName,
    T_SemanticRawNameList
)
from sciencebeam_parser.document.tei_document import TeiDocument, get_tei_for_semantic_document
from sciencebeam_parser.document.layout_document import LayoutDocument
from sciencebeam_parser.models.segmentation.model import SegmentationModel
from sciencebeam_parser.models.header.model import HeaderModel
from sciencebeam_parser.models.name.model import NameModel
from sciencebeam_parser.models.affiliation_address.model import AffiliationAddressModel
from sciencebeam_parser.models.fulltext.model import FullTextModel
from sciencebeam_parser.models.figure.model import FigureModel
from sciencebeam_parser.models.table.model import TableModel
from sciencebeam_parser.models.reference_segmenter.model import ReferenceSegmenterModel
from sciencebeam_parser.models.citation.model import CitationModel
from sciencebeam_parser.processors.ref_matching import (
    ChainedContentIdMatcher,
    ContentIdMatcher,
    PartialContentIdMatcher,
    SimpleContentIdMatcher
)


LOGGER = logging.getLogger(__name__)


@dataclass
class FullTextModels:
    segmentation_model: SegmentationModel
    header_model: HeaderModel
    name_header_model: NameModel
    name_citation_model: NameModel
    affiliation_address_model: AffiliationAddressModel
    fulltext_model: FullTextModel
    figure_model: FigureModel
    table_model: TableModel
    reference_segmenter_model: ReferenceSegmenterModel
    citation_model: CitationModel


T_Model = TypeVar('T_Model', bound=Model)


def load_model(
    app_config: AppConfig,
    app_context: AppContext,
    model_name: str,
    model_class: Type[T_Model]
) -> T_Model:
    models_config = app_config['models']
    model_config = models_config[model_name]
    model = model_class(
        get_model_impl_factory_for_config(
            model_config,
            app_context=app_context
        ),
        model_config=model_config
    )
    return model


def load_models(app_config: AppConfig, app_context: AppContext) -> FullTextModels:
    segmentation_model = load_model(
        app_config, app_context, 'segmentation', SegmentationModel
    )
    header_model = load_model(
        app_config, app_context, 'header', HeaderModel
    )
    name_header_model = load_model(
        app_config, app_context, 'name_header', NameModel
    )
    name_citation_model = load_model(
        app_config, app_context, 'name_citation', NameModel
    )
    affiliation_address_model = load_model(
        app_config, app_context, 'affiliation_address', AffiliationAddressModel
    )
    fulltext_model = load_model(
        app_config, app_context, 'fulltext', FullTextModel
    )
    figure_model = load_model(
        app_config, app_context, 'figure', FigureModel
    )
    table_model = load_model(
        app_config, app_context, 'table', TableModel
    )
    reference_segmenter_model = load_model(
        app_config, app_context, 'reference_segmenter', ReferenceSegmenterModel
    )
    citation_model = load_model(
        app_config, app_context, 'citation', CitationModel
    )
    return FullTextModels(
        segmentation_model=segmentation_model,
        header_model=header_model,
        name_header_model=name_header_model,
        name_citation_model=name_citation_model,
        affiliation_address_model=affiliation_address_model,
        fulltext_model=fulltext_model,
        figure_model=figure_model,
        table_model=table_model,
        reference_segmenter_model=reference_segmenter_model,
        citation_model=citation_model
    )


class FullTextProcessorConfig(NamedTuple):
    extract_citation_fields: bool = True
    extract_citation_authors: bool = True
    extract_citation_editors: bool = False
    extract_figure_fields: bool = True
    extract_table_fields: bool = True
    merge_raw_authors: bool = False

    @staticmethod
    def from_app_config(app_config: AppConfig) -> 'FullTextProcessorConfig':
        return FullTextProcessorConfig()._replace(
            **app_config.get('processors', {}).get('fulltext', {})
        )


class FullTextProcessor:
    def __init__(
        self,
        fulltext_models: FullTextModels,
        config: Optional[FullTextProcessorConfig] = None,
        app_features_context: AppFeaturesContext = DEFAULT_APP_FEATURES_CONTEXT
    ) -> None:
        self.fulltext_models = fulltext_models
        self.app_features_context = app_features_context
        if not config:
            config = FullTextProcessorConfig()
        self.config = config

    @property
    def segmentation_model(self) -> SegmentationModel:
        return self.fulltext_models.segmentation_model

    @property
    def header_model(self) -> HeaderModel:
        return self.fulltext_models.header_model

    @property
    def affiliation_address_model(self) -> AffiliationAddressModel:
        return self.fulltext_models.affiliation_address_model

    @property
    def name_header_model(self) -> NameModel:
        return self.fulltext_models.name_header_model

    @property
    def name_citation_model(self) -> NameModel:
        return self.fulltext_models.name_citation_model

    @property
    def fulltext_model(self) -> FullTextModel:
        return self.fulltext_models.fulltext_model

    @property
    def figure_model(self) -> FigureModel:
        return self.fulltext_models.figure_model

    @property
    def table_model(self) -> TableModel:
        return self.fulltext_models.table_model

    @property
    def reference_segmenter_model(self) -> ReferenceSegmenterModel:
        return self.fulltext_models.reference_segmenter_model

    @property
    def citation_model(self) -> CitationModel:
        return self.fulltext_models.citation_model

    def get_semantic_document_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> SemanticDocument:
        segmentation_label_result = self.segmentation_model.get_label_layout_document_result(
            layout_document,
            app_features_context=self.app_features_context
        )
        header_layout_document = segmentation_label_result.get_filtered_document_by_label(
            '<header>'
        ).remove_empty_blocks()
        LOGGER.debug('header_layout_document: %s', header_layout_document)
        document = SemanticDocument()
        if header_layout_document.pages:
            labeled_layout_tokens = self.header_model.predict_labels_for_layout_document(
                header_layout_document,
                app_features_context=self.app_features_context
            )
            LOGGER.debug('labeled_layout_tokens: %r', labeled_layout_tokens)
            entity_blocks = self.header_model.iter_entity_layout_blocks_for_labeled_layout_tokens(
                labeled_layout_tokens
            )
            self.header_model.update_semantic_document_with_entity_blocks(
                document, entity_blocks
            )
            self._process_raw_authors(document.front)
            self._process_raw_affiliations(document)

        self._update_semantic_section_using_segmentation_result_and_fulltext_model(
            document.body_section,
            segmentation_label_result,
            '<body>',
            SemanticSectionTypes.OTHER
        )
        self._update_semantic_section_using_segmentation_result_and_fulltext_model(
            document.back_section,
            segmentation_label_result,
            '<acknowledgement>',
            SemanticSectionTypes.ACKNOWLEDGEMENT
        )
        self._update_semantic_section_using_segmentation_result_and_fulltext_model(
            document.back_section,
            segmentation_label_result,
            '<annex>',
            SemanticSectionTypes.OTHER
        )
        self._extract_raw_references_from_segmentation(
            semantic_document=document,
            segmentation_label_result=segmentation_label_result
        )
        if self.config.extract_citation_fields:
            self._extract_reference_fields_from_raw_references(
                semantic_document=document
            )
            if self.config.extract_citation_authors or self.config.extract_citation_editors:
                self._extract_reference_name_lists_from_raw_references(
                    semantic_document=document
                )
            references = list(document.iter_by_type_recursively(SemanticReference))
            ref_citations = list(document.iter_by_type_recursively(SemanticReferenceCitation))
            self._assign_content_ids(references, iter(iter_ids('b')))
            self._assign_target_content_ids(ref_citations, ChainedContentIdMatcher([
                SimpleContentIdMatcher(
                    self._get_semantic_content_text_by_content_id(references, SemanticLabel)
                ),
                PartialContentIdMatcher(
                    self._get_semantic_content_text_by_content_id(
                        references, SemanticRawReferenceText
                    )
                )
            ]))
        if self.config.extract_figure_fields:
            self._extract_figure_fields_from_raw_figures(semantic_document=document)
            figures = list(document.iter_by_type_recursively(SemanticFigure))
            figure_citations = list(document.iter_by_type_recursively(SemanticFigureCitation))
            self._assign_content_ids(figures, iter(iter_ids('fig_')))
            self._assign_target_content_ids(figure_citations, SimpleContentIdMatcher(
                self._get_semantic_content_text_by_content_id(figures, SemanticLabel)
            ))
        if self.config.extract_table_fields:
            self._extract_table_fields_from_raw_tables(semantic_document=document)
            tables = list(document.iter_by_type_recursively(SemanticTable))
            table_citations = list(document.iter_by_type_recursively(SemanticTableCitation))
            self._assign_content_ids(tables, iter(iter_ids('tab_')))
            self._assign_target_content_ids(table_citations, SimpleContentIdMatcher(
                self._get_semantic_content_text_by_content_id(tables, SemanticLabel)
            ))
        return document

    def _assign_content_ids(
        self,
        semantic_content_iterable: Iterable[SemanticMixedContentWrapper],
        content_id_iterator: Iterator[str]
    ):
        for semantic_content in semantic_content_iterable:
            semantic_content.content_id = next(content_id_iterator)

    def _get_semantic_content_text_by_content_id(
        self,
        semantic_content_iterable: Iterable[SemanticMixedContentWrapper],
        type_: Type[SemanticContentWrapper]
    ) -> Mapping[str, str]:
        d = {}
        for semantic_content in semantic_content_iterable:
            if not semantic_content.content_id:
                continue
            text = semantic_content.get_text_by_type(type_)
            if not text:
                continue
            d[semantic_content.content_id] = text
        return d

    def _assign_target_content_ids(
        self,
        semantic_content_iterable: Iterable[SemanticCitation],
        content_id_matcher: ContentIdMatcher
    ):
        for citation in semantic_content_iterable:
            content_id = content_id_matcher.get_id_by_text(citation.get_text())
            if content_id:
                citation.target_content_id = content_id

    def _process_raw_authors(self, semantic_parent: SemanticMixedContentWrapper):
        result_content: List[SemanticContentWrapper] = []
        raw_authors: List[SemanticRawAuthors] = []
        for semantic_content in semantic_parent:
            if isinstance(semantic_content, SemanticRawAuthors):
                raw_authors.append(semantic_content)
                continue
            result_content.append(semantic_content)
        if raw_authors:
            if self.config.merge_raw_authors:
                raw_authors_layout_documents = [
                    LayoutDocument.for_blocks([
                        block
                        for raw_author in raw_authors
                        for block in raw_author.iter_blocks()
                    ])
                ]
            else:
                raw_authors_layout_documents = [
                    LayoutDocument.for_blocks(list(raw_author.iter_blocks()))
                    for raw_author in raw_authors
                ]
            labeled_layout_tokens_list = self.name_header_model.predict_labels_for_layout_documents(
                raw_authors_layout_documents,
                app_features_context=self.app_features_context
            )
            LOGGER.debug('labeled_layout_tokens_list (author): %r', labeled_layout_tokens_list)
            authors_iterable = (
                author
                for labeled_layout_tokens in labeled_layout_tokens_list
                for author in (
                    self.name_header_model.iter_semantic_content_for_labeled_layout_tokens(
                        labeled_layout_tokens
                    )
                )
            )
            for author in authors_iterable:
                result_content.append(author)
        semantic_parent.mixed_content = result_content

    def _process_raw_affiliations(self, semantic_document: SemanticDocument):
        result_content: List[SemanticContentWrapper] = []
        raw_aff_address_list: List[SemanticRawAffiliationAddress] = []
        for semantic_content in semantic_document.front:
            if isinstance(semantic_content, SemanticRawAffiliationAddress):
                raw_aff_address_list.append(semantic_content)
                continue
            result_content.append(semantic_content)
        if raw_aff_address_list:
            raw_aff_layout_documents = [
                LayoutDocument.for_blocks(list(raw_aff_or_address.iter_blocks()))
                for raw_aff_or_address in raw_aff_address_list
            ]
            labeled_layout_tokens_list = (
                self.affiliation_address_model
                .predict_labels_for_layout_documents(
                    raw_aff_layout_documents,
                    app_features_context=self.app_features_context
                )
            )
            LOGGER.debug('labeled_layout_tokens_list (aff): %r', labeled_layout_tokens_list)
            aff_iterable = (
                aff
                for labeled_layout_tokens in labeled_layout_tokens_list
                for aff in (
                    self.affiliation_address_model
                    .iter_semantic_content_for_labeled_layout_tokens(labeled_layout_tokens)
                )
            )
            for aff in aff_iterable:
                result_content.append(aff)
        semantic_document.front.mixed_content = result_content
        self._assign_content_ids(
            semantic_document.front.iter_by_type(SemanticAffiliationAddress),
            iter(iter_ids('aff'))
        )

    def _extract_raw_references_from_segmentation(
        self,
        semantic_document: SemanticDocument,
        segmentation_label_result: LayoutDocumentLabelResult
    ):
        references_layout_document = segmentation_label_result.get_filtered_document_by_label(
            '<references>'
        ).remove_empty_blocks()
        LOGGER.debug('references_layout_document: %s', references_layout_document)
        if not references_layout_document:
            return
        labeled_layout_tokens = self.reference_segmenter_model.predict_labels_for_layout_document(
            references_layout_document,
            app_features_context=self.app_features_context
        )
        LOGGER.debug('labeled_layout_tokens: %r', labeled_layout_tokens)
        semantic_content_iterable = (
            self.reference_segmenter_model
            .iter_semantic_content_for_labeled_layout_tokens(labeled_layout_tokens)
        )
        reference_list = SemanticReferenceList(list(semantic_content_iterable))
        semantic_document.back_section.add_content(reference_list)

    def _iter_parse_semantic_references(
        self,
        semantic_raw_references: List[SemanticRawReference]
    ) -> Iterable[Union[SemanticReference, SemanticInvalidReference]]:
        layout_documents = [
            LayoutDocument.for_blocks([semantic_raw_reference.merged_block])
            for semantic_raw_reference in semantic_raw_references
        ]
        labeled_layout_tokens_list = (
            self.citation_model
            .predict_labels_for_layout_documents(
                layout_documents,
                app_features_context=self.app_features_context
            )
        )
        LOGGER.debug('labeled_layout_tokens_list: %r', labeled_layout_tokens_list)
        for labeled_layout_tokens, semantic_raw_reference in zip(
            labeled_layout_tokens_list, semantic_raw_references
        ):
            semantic_content_iterable = (
                self.citation_model
                .iter_semantic_content_for_labeled_layout_tokens(
                    labeled_layout_tokens,
                    semantic_raw_reference=semantic_raw_reference
                )
            )
            ref: Optional[Union[SemanticReference, SemanticInvalidReference]] = None
            for semantic_content in semantic_content_iterable:
                if isinstance(semantic_content, (SemanticReference, SemanticInvalidReference)):
                    ref = semantic_content
            if not ref:
                raise AssertionError('no semantic reference extracted')
            yield ref

    def _extract_reference_fields_from_raw_references(
        self,
        semantic_document: SemanticDocument
    ):
        reference_lists = list(semantic_document.back_section.iter_by_type(
            SemanticReferenceList
        ))
        semantic_raw_references = [
            raw_reference
            for reference_list in reference_lists
            for raw_reference in reference_list.iter_by_type(SemanticRawReference)
        ]
        semantic_references = list(self._iter_parse_semantic_references(
            semantic_raw_references
        ))
        LOGGER.debug('semantic_references: %r', semantic_references)
        semantic_reference_by_semantic_raw_reference_id = {
            id(semantic_raw_reference): semantic_reference
            for semantic_raw_reference, semantic_reference in zip(
                semantic_raw_references, semantic_references
            )
        }
        LOGGER.debug(
            'semantic_reference_by_semantic_raw_reference_id keys: %s',
            semantic_reference_by_semantic_raw_reference_id.keys()
        )
        for reference_list in reference_lists:
            updated_content: List[SemanticContentWrapper] = []
            for semantic_content in reference_list:
                if isinstance(semantic_content, SemanticRawReference):
                    semantic_reference = semantic_reference_by_semantic_raw_reference_id[
                        id(semantic_content)
                    ]
                    updated_content.append(semantic_reference)
                    continue
                updated_content.append(semantic_content)
            reference_list.mixed_content = updated_content

    def _iter_parse_semantic_name_lists(
        self,
        semantic_raw_name_lists: Sequence[T_SemanticRawNameList],
        name_type: Type[T_SemanticName]
    ) -> Iterable[Tuple[T_SemanticRawNameList, List[SemanticContentWrapper]]]:
        layout_documents = [
            LayoutDocument.for_blocks([semantic_raw_name_list.merged_block])
            for semantic_raw_name_list in semantic_raw_name_lists
        ]
        labeled_layout_tokens_list = (
            self.name_citation_model
            .predict_labels_for_layout_documents(
                layout_documents,
                app_features_context=self.app_features_context
            )
        )
        LOGGER.debug('labeled_layout_tokens_list: %r', labeled_layout_tokens_list)
        for labeled_layout_tokens, semantic_raw_name_list in zip(
            labeled_layout_tokens_list, semantic_raw_name_lists
        ):
            semantic_content_iterable = (
                self.name_citation_model
                .iter_semantic_content_for_labeled_layout_tokens(
                    labeled_layout_tokens,
                    name_type=name_type
                )
            )
            yield semantic_raw_name_list, list(semantic_content_iterable)

    def _extract_reference_name_lists_from_raw_references(
        self,
        semantic_document: SemanticDocument
    ):
        reference_lists = list(semantic_document.back_section.iter_by_type(
            SemanticReferenceList
        ))
        ref_list = [
            ref
            for reference_list in reference_lists
            for ref in reference_list.iter_by_type(SemanticReference)
        ]
        if self.config.extract_citation_authors:
            raw_authors = [
                raw_author
                for ref in ref_list
                for raw_author in ref.iter_by_type(SemanticRawAuthors)
            ]
        else:
            raw_authors = []
        if self.config.extract_citation_editors:
            raw_editors = [
                raw_author
                for ref in ref_list
                for raw_author in ref.iter_by_type(SemanticRawEditors)
            ]
        else:
            raw_editors = []
        content_list_by_raw_author_id = {
            id(raw_author): content_list
            for raw_author, content_list in (
                self._iter_parse_semantic_name_lists(raw_authors, name_type=SemanticAuthor)
            )
        }
        content_list_by_raw_editor_id = {
            id(raw_author): content_list
            for raw_author, content_list in (
                self._iter_parse_semantic_name_lists(raw_editors, name_type=SemanticEditor)
            )
        }
        LOGGER.debug(
            'content_list_by_raw_author_id keys: %s',
            content_list_by_raw_author_id.keys()
        )
        LOGGER.debug(
            'content_list_by_raw_editor_id keys: %s',
            content_list_by_raw_editor_id.keys()
        )
        for reference_list in reference_lists:
            for semantic_content in reference_list:
                if isinstance(semantic_content, SemanticReference):
                    if self.config.extract_citation_authors:
                        semantic_content.flat_map_inplace_by_type(
                            SemanticRawAuthors,
                            lambda raw_author: content_list_by_raw_author_id[
                                id(raw_author)
                            ]
                        )
                    if self.config.extract_citation_editors:
                        semantic_content.flat_map_inplace_by_type(
                            SemanticRawEditors,
                            lambda raw_editor: content_list_by_raw_editor_id[
                                id(raw_editor)
                            ]
                        )

    def _iter_parse_semantic_content_lists(
        self,
        semantic_raw_content_lists: Sequence[T_SemanticContentWrapper],
        model: Model
    ) -> Iterable[Tuple[T_SemanticContentWrapper, List[SemanticContentWrapper]]]:
        layout_documents = [
            LayoutDocument.for_blocks([semantic_raw_name_list.merged_block])
            for semantic_raw_name_list in semantic_raw_content_lists
        ]
        labeled_layout_tokens_list = (
            model
            .predict_labels_for_layout_documents(
                layout_documents,
                app_features_context=self.app_features_context
            )
        )
        LOGGER.debug('labeled_layout_tokens_list: %r', labeled_layout_tokens_list)
        for labeled_layout_tokens, semantic_raw_name_list in zip(
            labeled_layout_tokens_list, semantic_raw_content_lists
        ):
            semantic_content_iterable = (
                model
                .iter_semantic_content_for_labeled_layout_tokens(
                    labeled_layout_tokens
                )
            )
            yield semantic_raw_name_list, list(semantic_content_iterable)

    def _extract_semantic_content_from_raw_content(
        self,
        semantic_document: SemanticDocument,
        semantic_type: Type[T_SemanticContentWrapper],
        model: Model
    ):
        parents = [
            parent
            for root in [
                semantic_document.body_section,
                semantic_document.back_section
            ]
            for parent in root.iter_parent_by_semantic_type_recursively(
                semantic_type
            )
        ]
        raw_content_lists = [
            raw_content
            for parent in parents
            for raw_content in parent.iter_by_type(semantic_type)
        ]
        content_list_by_raw_content_id = {
            id(raw_content): content_list
            for raw_content, content_list in (
                self._iter_parse_semantic_content_lists(
                    raw_content_lists,
                    model
                )
            )
        }
        LOGGER.debug(
            'content_list_by_raw_content_id keys: %s',
            content_list_by_raw_content_id.keys()
        )
        for parent in parents:
            parent.flat_map_inplace_by_type(
                semantic_type,
                lambda raw_content: content_list_by_raw_content_id[
                    id(raw_content)
                ]
            )

    def _extract_figure_fields_from_raw_figures(
        self,
        semantic_document: SemanticDocument
    ):
        self._extract_semantic_content_from_raw_content(
            semantic_document,
            SemanticRawFigure,
            self.figure_model
        )

    def _extract_table_fields_from_raw_tables(
        self,
        semantic_document: SemanticDocument
    ):
        self._extract_semantic_content_from_raw_content(
            semantic_document,
            SemanticRawTable,
            self.table_model
        )

    def _update_semantic_section_using_segmentation_result_and_fulltext_model(
        self,
        semantic_section: SemanticSection,
        segmentation_label_result: LayoutDocumentLabelResult,
        segmentation_tag: str,
        section_type: str
    ):
        layout_document = segmentation_label_result.get_filtered_document_by_label(
            segmentation_tag
        ).remove_empty_blocks()
        self._update_semantic_section_using_layout_document_and_fulltext_model(
            semantic_section,
            layout_document,
            section_name=segmentation_tag,
            section_type=section_type
        )

    def _update_semantic_section_using_layout_document_and_fulltext_model(
        self,
        semantic_section: SemanticSection,
        layout_document: LayoutDocument,
        section_name: str,
        section_type: str
    ):
        LOGGER.debug('layout_document (%r): %s', section_name, layout_document)
        if not layout_document.pages:
            return
        labeled_layout_tokens = self.fulltext_model.predict_labels_for_layout_document(
            layout_document,
            app_features_context=self.app_features_context
        )
        LOGGER.debug('labeled_layout_tokens (%r): %r', section_name, labeled_layout_tokens)
        entity_blocks = self.fulltext_model.iter_entity_layout_blocks_for_labeled_layout_tokens(
            labeled_layout_tokens
        )
        self.fulltext_model.update_section_with_entity_blocks(
            semantic_section,
            entity_blocks,
            section_type=section_type
        )

    def get_tei_document_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> TeiDocument:
        return get_tei_for_semantic_document(
            self.get_semantic_document_for_layout_document(
                layout_document
            )
        )
