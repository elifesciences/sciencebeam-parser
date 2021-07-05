import logging
from dataclasses import dataclass
from typing import Iterable, List, NamedTuple, Optional, Sequence, Tuple, Type, Union

from pygrobid.config.config import AppConfig
from pygrobid.models.model import LayoutDocumentLabelResult
from pygrobid.models.model_impl_factory import get_delft_model_impl_factory_for_config

from pygrobid.document.semantic_document import (
    SemanticAuthor,
    SemanticContentWrapper,
    SemanticDocument,
    SemanticEditor,
    SemanticMixedContentWrapper,
    SemanticRawAddress,
    SemanticRawAffiliation,
    SemanticRawAuthors,
    SemanticRawEditors,
    SemanticRawReference,
    SemanticReference,
    SemanticReferenceList,
    SemanticSection,
    SemanticSectionTypes,
    T_SemanticName,
    T_SemanticRawNameList
)
from pygrobid.document.tei_document import TeiDocument, get_tei_for_semantic_document
from pygrobid.document.layout_document import LayoutDocument
from pygrobid.models.segmentation.model import SegmentationModel
from pygrobid.models.header.model import HeaderModel
from pygrobid.models.name.model import NameModel
from pygrobid.models.affiliation_address.model import AffiliationAddressModel
from pygrobid.models.fulltext.model import FullTextModel
from pygrobid.models.reference_segmenter.model import ReferenceSegmenterModel
from pygrobid.models.citation.model import CitationModel


LOGGER = logging.getLogger(__name__)


@dataclass
class FullTextModels:
    segmentation_model: SegmentationModel
    header_model: HeaderModel
    name_header_model: NameModel
    name_citation_model: NameModel
    affiliation_address_model: AffiliationAddressModel
    fulltext_model: FullTextModel
    reference_segmenter_model: ReferenceSegmenterModel
    citation_model: CitationModel


def load_models(app_config: AppConfig) -> FullTextModels:
    models_config = app_config['models']
    segmentation_model = SegmentationModel(get_delft_model_impl_factory_for_config(
        models_config['segmentation']
    ))
    header_model = HeaderModel(get_delft_model_impl_factory_for_config(
        models_config['header']
    ))
    name_header_model = NameModel(get_delft_model_impl_factory_for_config(
        models_config['name-header']
    ))
    name_citation_model = NameModel(get_delft_model_impl_factory_for_config(
        models_config['name-citation']
    ))
    affiliation_address_model = AffiliationAddressModel(get_delft_model_impl_factory_for_config(
        models_config['affiliation-address']
    ))
    fulltext_model = FullTextModel(get_delft_model_impl_factory_for_config(
        models_config['fulltext']
    ))
    reference_segmenter_model = ReferenceSegmenterModel(get_delft_model_impl_factory_for_config(
        models_config['reference-segmenter']
    ))
    citation_model = CitationModel(get_delft_model_impl_factory_for_config(
        models_config['citation']
    ))
    return FullTextModels(
        segmentation_model=segmentation_model,
        header_model=header_model,
        name_header_model=name_header_model,
        name_citation_model=name_citation_model,
        affiliation_address_model=affiliation_address_model,
        fulltext_model=fulltext_model,
        reference_segmenter_model=reference_segmenter_model,
        citation_model=citation_model
    )


class FullTextProcessorConfig(NamedTuple):
    extract_citation_fields: bool = True
    extract_citation_authors: bool = True
    extract_citation_editors: bool = False


class FullTextProcessor:
    def __init__(
        self,
        fulltext_models: FullTextModels,
        config: Optional[FullTextProcessorConfig] = None
    ) -> None:
        self.fulltext_models = fulltext_models
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
            layout_document
        )
        header_layout_document = segmentation_label_result.get_filtered_document_by_label(
            '<header>'
        ).remove_empty_blocks()
        LOGGER.debug('header_layout_document: %s', header_layout_document)
        document = SemanticDocument()
        if header_layout_document.pages:
            labeled_layout_tokens = self.header_model.predict_labels_for_layout_document(
                header_layout_document
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
        return document

    def _process_raw_authors(self, semantic_parent: SemanticMixedContentWrapper):
        result_content: List[SemanticContentWrapper] = []
        raw_authors: List[SemanticRawAuthors] = []
        for semantic_content in semantic_parent:
            if isinstance(semantic_content, SemanticRawAuthors):
                raw_authors.append(semantic_content)
                continue
            result_content.append(semantic_content)
        if raw_authors:
            raw_authors_layout_document = LayoutDocument.for_blocks([
                block
                for raw_author in raw_authors
                for block in raw_author.iter_blocks()
            ])
            labeled_layout_tokens = self.name_header_model.predict_labels_for_layout_document(
                raw_authors_layout_document
            )
            LOGGER.debug('labeled_layout_tokens (author): %r', labeled_layout_tokens)
            authors_iterable = (
                self.name_header_model.iter_semantic_content_for_labeled_layout_tokens(
                    labeled_layout_tokens
                )
            )
            for author in authors_iterable:
                result_content.append(author)
        semantic_parent.mixed_content = result_content

    def _process_raw_affiliations(self, semantic_document: SemanticDocument):
        result_content: List[SemanticContentWrapper] = []
        raw_aff_address_list: List[Union[SemanticRawAffiliation, SemanticRawAddress]] = []
        for semantic_content in semantic_document.front:
            if isinstance(semantic_content, SemanticRawAffiliation):
                raw_aff_address_list.append(semantic_content)
                continue
            if isinstance(semantic_content, SemanticRawAddress):
                raw_aff_address_list.append(semantic_content)
                continue
            result_content.append(semantic_content)
        if raw_aff_address_list:
            raw_aff_layout_document = LayoutDocument.for_blocks([
                block
                for raw_aff_or_address in raw_aff_address_list
                for block in raw_aff_or_address.iter_blocks()
            ])
            labeled_layout_tokens = (
                self.affiliation_address_model
                .predict_labels_for_layout_document(
                    raw_aff_layout_document
                )
            )
            LOGGER.debug('labeled_layout_tokens (author): %r', labeled_layout_tokens)
            aff_iterable = (
                self.affiliation_address_model.iter_semantic_content_for_labeled_layout_tokens(
                    labeled_layout_tokens
                )
            )
            for aff in aff_iterable:
                result_content.append(aff)
        semantic_document.front.mixed_content = result_content

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
            references_layout_document
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
    ) -> Iterable[SemanticReference]:
        layout_documents = [
            LayoutDocument.for_blocks([semantic_raw_reference.merged_block])
            for semantic_raw_reference in semantic_raw_references
        ]
        labeled_layout_tokens_list = (
            self.citation_model
            .predict_labels_for_layout_documents(layout_documents)
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
            ref: Optional[SemanticReference] = None
            for semantic_content in semantic_content_iterable:
                if isinstance(semantic_content, SemanticReference):
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
            .predict_labels_for_layout_documents(layout_documents)
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
            layout_document
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
