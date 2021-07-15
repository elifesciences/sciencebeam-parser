import logging
from typing import Dict, Iterable, List, Mapping, Union
from unittest.mock import MagicMock

import pytest

from pygrobid.document.layout_document import LayoutBlock, LayoutDocument, LayoutPage
from pygrobid.document.semantic_document import (
    SemanticAffiliationAddress,
    SemanticAuthor,
    SemanticCaption,
    SemanticCountry,
    SemanticEditor,
    SemanticFigure,
    SemanticFigureCitation,
    SemanticInstitution,
    SemanticLabel,
    SemanticMarker,
    SemanticRawReference,
    SemanticRawReferenceText,
    SemanticReference,
    SemanticReferenceCitation,
    SemanticReferenceList,
    SemanticSectionTypes,
    SemanticTable,
    SemanticTableCitation,
    SemanticTitle,
    iter_by_semantic_type_recursively
)
from pygrobid.models.model import NEW_DOCUMENT_MARKER, NewDocumentMarker
from pygrobid.models.model import LayoutModelLabel, Model
from pygrobid.models.segmentation.model import SegmentationModel
from pygrobid.models.header.model import HeaderModel
from pygrobid.models.affiliation_address.model import AffiliationAddressModel
from pygrobid.models.name.model import NameModel
from pygrobid.models.fulltext.model import FullTextModel
from pygrobid.models.figure.model import FigureModel
from pygrobid.models.table.model import TableModel
from pygrobid.models.reference_segmenter.model import ReferenceSegmenterModel
from pygrobid.models.citation.model import CitationModel
from pygrobid.processors.fulltext import (
    FullTextProcessor,
    FullTextModels,
    FullTextProcessorConfig
)


LOGGER = logging.getLogger(__name__)


LayoutTokenId = int


def get_label_by_layout_token_for_block(
    layout_block: LayoutBlock,
    label: str
) -> Dict[LayoutTokenId, str]:
    return {
        id(layout_token): 'B-' + label if index == 0 else 'I-' + label
        for index, layout_token in enumerate(layout_block.iter_all_tokens())
    }


class MockDelftModelWrapper:
    def __init__(self, model_wrapper: Model):
        self._model_wrapper = model_wrapper
        self._label_by_layout_token: Dict[LayoutTokenId, str] = {}
        self._default_label = 'O'
        model_wrapper._model_impl = MagicMock(name='model_impl')
        model_wrapper._iter_label_layout_documents = (  # type: ignore
            self._iter_label_layout_documents
        )

    def update_label_by_layout_tokens(
        self,
        label_by_layout_token: Mapping[LayoutTokenId, str]
    ):
        self._label_by_layout_token.update(label_by_layout_token)

    def update_label_by_layout_block(
        self,
        layout_block: LayoutBlock,
        label: str
    ):
        self.update_label_by_layout_tokens(
            get_label_by_layout_token_for_block(layout_block, label)
        )

    def _iter_label_layout_documents(
        self,
        layout_documents: Iterable[LayoutDocument]
    ) -> Iterable[Union[LayoutModelLabel, NewDocumentMarker]]:
        for index, layout_document in enumerate(layout_documents):
            if index > 0:
                yield NEW_DOCUMENT_MARKER
            yield from self._iter_label_layout_document(layout_document)

    def _iter_label_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> Iterable[LayoutModelLabel]:
        data_generator = self._model_wrapper.get_data_generator()
        LOGGER.debug('_label_by_layout_token.keys: %s', self._label_by_layout_token.keys())
        for model_data in data_generator.iter_model_data_for_layout_document(layout_document):
            if model_data.layout_token:
                label = self._label_by_layout_token.get(
                    id(model_data.layout_token),
                    self._default_label
                )
                LOGGER.debug('id(layout_token)=%r, label=%r', id(model_data.layout_token), label)
            else:
                assert model_data.layout_line
                first_layout_token = model_data.layout_line.tokens[0]
                label = self._label_by_layout_token.get(
                    id(first_layout_token),
                    self._default_label
                )
                LOGGER.debug('id(first_layout_token)=%r, label=%r', id(first_layout_token), label)
            yield LayoutModelLabel(
                label=label,
                label_token_text='dummy',
                layout_line=model_data.layout_line,
                layout_token=model_data.layout_token
            )


class MockFullTextModels(FullTextModels):
    def __init__(self):
        model_impl_mock = MagicMock('model_impl')
        super().__init__(
            segmentation_model=SegmentationModel(model_impl_mock),
            header_model=HeaderModel(model_impl_mock),
            name_header_model=NameModel(model_impl_mock),
            name_citation_model=NameModel(model_impl_mock),
            affiliation_address_model=AffiliationAddressModel(model_impl_mock),
            fulltext_model=FullTextModel(model_impl_mock),
            figure_model=FigureModel(model_impl_mock),
            table_model=TableModel(model_impl_mock),
            reference_segmenter_model=ReferenceSegmenterModel(model_impl_mock),
            citation_model=CitationModel(model_impl_mock)
        )
        self.segmentation_model_mock = MockDelftModelWrapper(self.segmentation_model)
        self.header_model_mock = MockDelftModelWrapper(self.header_model)
        self.name_header_model_mock = MockDelftModelWrapper(self.name_header_model)
        self.name_citation_model_mock = MockDelftModelWrapper(self.name_citation_model)
        self.affiliation_address_model_mock = MockDelftModelWrapper(
            self.affiliation_address_model
        )
        self.fulltext_model_mock = MockDelftModelWrapper(self.fulltext_model)
        self.figure_model_mock = MockDelftModelWrapper(self.figure_model)
        self.table_model_mock = MockDelftModelWrapper(self.table_model)
        self.reference_segmenter_model_mock = MockDelftModelWrapper(self.reference_segmenter_model)
        self.citation_model_mock = MockDelftModelWrapper(self.citation_model)


@pytest.fixture(name='fulltext_models_mock')
def _fulltext_models() -> MockFullTextModels:
    return MockFullTextModels()


def _get_layout_model_labels_for_block(
    layout_block: LayoutBlock,
    label: str
) -> List[LayoutModelLabel]:
    return [
        LayoutModelLabel(
            label=label,
            label_token_text=layout_token.text,
            layout_line=layout_line,
            layout_token=layout_token
        )
        for layout_line in layout_block.lines
        for layout_token in layout_line.tokens
    ]


class TestFullTextProcessor:
    def test_should_not_fail_with_empty_document(
        self, fulltext_models_mock: MockFullTextModels
    ):
        fulltext_processor = FullTextProcessor(fulltext_models_mock)
        layout_document = LayoutDocument(pages=[])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        assert semantic_document is not None

    def test_should_extract_from_document(
        self, fulltext_models_mock: MockFullTextModels
    ):
        fulltext_processor = FullTextProcessor(fulltext_models_mock)
        header_block = LayoutBlock.for_text('This is the header')
        body_block = LayoutBlock.for_text('This is the body')
        acknowledgment_block = LayoutBlock.for_text('Some acknowledgement')
        back_block = LayoutBlock.for_text('This is the back')

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        header_model_mock = fulltext_models_mock.header_model_mock
        fulltext_model_mock = fulltext_models_mock.fulltext_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            header_block, '<header>'
        )
        segmentation_model_mock.update_label_by_layout_block(
            body_block, '<body>'
        )
        segmentation_model_mock.update_label_by_layout_block(
            acknowledgment_block, '<acknowledgement>'
        )
        segmentation_model_mock.update_label_by_layout_block(
            back_block, '<annex>'
        )

        header_model_mock.update_label_by_layout_block(
            header_block, '<title>'
        )

        fulltext_model_mock.update_label_by_layout_block(
            body_block, '<paragraph>'
        )
        fulltext_model_mock.update_label_by_layout_block(
            acknowledgment_block, '<paragraph>'
        )
        fulltext_model_mock.update_label_by_layout_block(
            back_block, '<paragraph>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            header_block,
            body_block,
            acknowledgment_block,
            back_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        assert semantic_document is not None
        assert semantic_document.front.get_text() == header_block.text
        assert semantic_document.front.get_text_by_type(SemanticTitle) == header_block.text
        assert semantic_document.body_section.get_text() == body_block.text
        assert semantic_document.back_section.view_by_section_type(
            SemanticSectionTypes.OTHER
        ).get_text() == back_block.text
        assert semantic_document.back_section.view_by_section_type(
            SemanticSectionTypes.ACKNOWLEDGEMENT
        ).get_text() == acknowledgment_block.text

    def test_should_extract_acknowledgement_only(
        self, fulltext_models_mock: MockFullTextModels
    ):
        fulltext_processor = FullTextProcessor(fulltext_models_mock)
        acknowledgment_block = LayoutBlock.for_text('Some acknowledgement')

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        fulltext_model_mock = fulltext_models_mock.fulltext_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            acknowledgment_block, '<acknowledgement>'
        )

        fulltext_model_mock.update_label_by_layout_block(
            acknowledgment_block, '<paragraph>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            acknowledgment_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        assert semantic_document is not None
        assert semantic_document.back_section.view_by_section_type(
            SemanticSectionTypes.ACKNOWLEDGEMENT
        ).get_text() == acknowledgment_block.text

    def test_should_extract_author_names_from_document(
        self, fulltext_models_mock: MockFullTextModels
    ):
        given_name_block = LayoutBlock.for_text('Given name')
        surname_block = LayoutBlock.for_text('Surname')
        authors_block = LayoutBlock.merge_blocks([given_name_block, surname_block])
        fulltext_processor = FullTextProcessor(fulltext_models_mock)
        header_block = authors_block

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        header_model_mock = fulltext_models_mock.header_model_mock
        name_header_model_mock = fulltext_models_mock.name_header_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            header_block, '<header>'
        )

        header_model_mock.update_label_by_layout_block(
            authors_block, '<author>'
        )

        name_header_model_mock.update_label_by_layout_block(
            given_name_block, '<forename>'
        )
        name_header_model_mock.update_label_by_layout_block(
            surname_block, '<surname>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            header_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        assert semantic_document is not None
        assert semantic_document.front.get_text() == authors_block.text
        assert (
            semantic_document.front
            .view_by_type(SemanticAuthor).get_text()
        ) == authors_block.text
        authors = semantic_document.front.authors
        assert len(authors) == 1
        assert authors[0].given_name_text == given_name_block.text
        assert authors[0].surname_text == surname_block.text

    def test_should_extract_author_names_separated_by_another_tag(
        self, fulltext_models_mock: MockFullTextModels
    ):
        given_name_block = LayoutBlock.for_text('Given name')
        surname_block = LayoutBlock.for_text('Surname')
        other_block = LayoutBlock.for_text('Other')
        authors_block = LayoutBlock.merge_blocks([
            given_name_block, other_block, surname_block
        ])
        fulltext_processor = FullTextProcessor(fulltext_models_mock)
        header_block = authors_block

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        header_model_mock = fulltext_models_mock.header_model_mock
        name_header_model_mock = fulltext_models_mock.name_header_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            header_block, '<header>'
        )

        header_model_mock.update_label_by_layout_block(
            given_name_block, '<author>'
        )
        header_model_mock.update_label_by_layout_block(
            surname_block, '<author>'
        )

        name_header_model_mock.update_label_by_layout_block(
            given_name_block, '<forename>'
        )
        name_header_model_mock.update_label_by_layout_block(
            surname_block, '<surname>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            header_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        assert semantic_document is not None
        authors = semantic_document.front.authors
        assert len(authors) == 1
        assert authors[0].given_name_text == given_name_block.text
        assert authors[0].surname_text == surname_block.text

    def test_should_extract_affiliation_address_from_document(  # pylint: disable=too-many-locals
        self, fulltext_models_mock: MockFullTextModels
    ):
        marker_block = LayoutBlock.for_text('1')
        institution_block = LayoutBlock.for_text('Institution1')
        country_block = LayoutBlock.for_text('Country1')
        aff_block = LayoutBlock.merge_blocks([marker_block, institution_block])
        address_block = LayoutBlock.merge_blocks([country_block])
        aff_address_block = LayoutBlock.merge_blocks([aff_block, address_block])
        fulltext_processor = FullTextProcessor(fulltext_models_mock)
        header_block = aff_address_block

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        header_model_mock = fulltext_models_mock.header_model_mock
        affiliation_address_model_mock = fulltext_models_mock.affiliation_address_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            header_block, '<header>'
        )

        header_model_mock.update_label_by_layout_block(
            aff_block, '<affiliation>'
        )
        header_model_mock.update_label_by_layout_block(
            address_block, '<address>'
        )

        affiliation_address_model_mock.update_label_by_layout_block(
            marker_block, '<marker>'
        )
        affiliation_address_model_mock.update_label_by_layout_block(
            institution_block, '<institution>'
        )
        affiliation_address_model_mock.update_label_by_layout_block(
            country_block, '<country>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            header_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        assert semantic_document is not None
        assert semantic_document.front.get_text() == aff_address_block.text
        assert (
            semantic_document.front
            .view_by_type(SemanticAffiliationAddress).get_text()
        ) == aff_address_block.text
        affiliations = list(semantic_document.front.iter_by_type(SemanticAffiliationAddress))
        assert len(affiliations) == 1
        assert affiliations[0].get_text_by_type(SemanticMarker) == marker_block.text
        assert affiliations[0].get_text_by_type(SemanticInstitution) == institution_block.text
        assert affiliations[0].get_text_by_type(SemanticCountry) == country_block.text
        assert affiliations[0].content_id == 'aff0'

    def test_should_not_merge_separate_raw_affiliations(  # pylint: disable=too-many-locals
        self, fulltext_models_mock: MockFullTextModels
    ):
        aff_suffix_texts = ['1', '2']
        institution_blocks = [
            LayoutBlock.for_text(f'Institution{t}')
            for t in aff_suffix_texts
        ]
        aff_blocks = institution_blocks
        aff_address_blocks = aff_blocks
        fulltext_processor = FullTextProcessor(fulltext_models_mock)
        header_block = LayoutBlock.merge_blocks(aff_address_blocks)

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        header_model_mock = fulltext_models_mock.header_model_mock
        affiliation_address_model_mock = fulltext_models_mock.affiliation_address_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            header_block, '<header>'
        )

        for aff_block in aff_blocks:
            header_model_mock.update_label_by_layout_block(
                aff_block, '<affiliation>'
            )

        for institution_block in institution_blocks:
            affiliation_address_model_mock.update_label_by_layout_block(
                institution_block, '<institution>'
            )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            header_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        assert semantic_document is not None
        affiliations = list(semantic_document.front.iter_by_type(SemanticAffiliationAddress))
        LOGGER.debug('affiliations: %r', affiliations)
        assert (
            [aff.get_text() for aff in affiliations]
            == [aff_block.text for aff_block in aff_blocks]
        )
        assert (
            [aff.content_id for aff in affiliations]
            == ['aff0', 'aff1']
        )

    def test_should_extract_raw_references_from_document(  # pylint: disable=too-many-locals
        self, fulltext_models_mock: MockFullTextModels
    ):
        label_block = LayoutBlock.for_text('1')
        ref_text_block = LayoutBlock.for_text('Reference 1')
        ref_block = LayoutBlock.merge_blocks([label_block, ref_text_block])
        fulltext_processor = FullTextProcessor(
            fulltext_models_mock,
            FullTextProcessorConfig(extract_citation_fields=False)
        )

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        reference_segmenter_model_mock = fulltext_models_mock.reference_segmenter_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            ref_block, '<references>'
        )

        reference_segmenter_model_mock.update_label_by_layout_block(
            label_block, '<label>'
        )
        reference_segmenter_model_mock.update_label_by_layout_block(
            ref_text_block, '<reference>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            ref_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        LOGGER.debug('semantic_document: %s', semantic_document)
        assert semantic_document is not None
        assert semantic_document.back_section.get_text() == ref_block.text
        reference_list = list(semantic_document.back_section.iter_by_type(SemanticReferenceList))
        assert len(reference_list) == 1
        references = list(reference_list[0].iter_by_type(SemanticRawReference))
        assert len(references) == 1
        ref = references[0]
        assert ref.get_text_by_type(SemanticLabel) == label_block.text
        assert ref.get_text_by_type(SemanticRawReferenceText) == ref_text_block.text
        assert ref.content_id == 'b0'

    def test_should_extract_references_fields_from_document(  # pylint: disable=too-many-locals
        self, fulltext_models_mock: MockFullTextModels
    ):
        other_body = LayoutBlock.for_text('the body')
        citation_block = LayoutBlock.for_text('1')
        body_block = LayoutBlock.merge_blocks([other_body, citation_block])
        label_block = LayoutBlock.for_text('1')
        ref_title_block = LayoutBlock.for_text('Reference Title 1')
        ref_text_block = LayoutBlock.merge_blocks([
            ref_title_block
        ])
        ref_block = LayoutBlock.merge_blocks([label_block, ref_text_block])
        fulltext_processor = FullTextProcessor(
            fulltext_models_mock,
            FullTextProcessorConfig(extract_citation_fields=True)
        )

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        fulltext_model_mock = fulltext_models_mock.fulltext_model_mock
        reference_segmenter_model_mock = fulltext_models_mock.reference_segmenter_model_mock
        citation_model_mock = fulltext_models_mock.citation_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            body_block, '<body>'
        )
        segmentation_model_mock.update_label_by_layout_block(
            ref_block, '<references>'
        )

        fulltext_model_mock.update_label_by_layout_block(
            other_body, '<section>'
        )
        fulltext_model_mock.update_label_by_layout_block(
            citation_block, '<citation_marker>'
        )

        reference_segmenter_model_mock.update_label_by_layout_block(
            label_block, '<label>'
        )
        reference_segmenter_model_mock.update_label_by_layout_block(
            ref_text_block, '<reference>'
        )

        citation_model_mock.update_label_by_layout_block(
            ref_title_block, '<title>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            body_block,
            ref_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        LOGGER.debug('semantic_document: %s', semantic_document)
        assert semantic_document is not None
        reference_list = list(semantic_document.back_section.iter_by_type(SemanticReferenceList))
        assert len(reference_list) == 1
        references = list(reference_list[0].iter_by_type(SemanticReference))
        assert len(references) == 1
        ref = references[0]
        assert ref.get_text_by_type(SemanticTitle) == ref_title_block.text
        assert ref.get_text_by_type(SemanticLabel) == label_block.text
        assert ref.get_text_by_type(SemanticRawReferenceText) == ref_text_block.text
        assert ref.content_id == 'b0'
        ref_citations = list(
            semantic_document.iter_by_type_recursively(SemanticReferenceCitation)
        )
        assert len(ref_citations) == 1
        assert ref_citations[0].target_content_id == 'b0'

    def test_should_extract_author_names_from_references_fields(  # pylint: disable=too-many-locals
        self, fulltext_models_mock: MockFullTextModels
    ):
        given_name_block = LayoutBlock.for_text('Given name')
        surname_block = LayoutBlock.for_text('Surname')
        other_block = LayoutBlock.for_text('Other')
        authors_block = LayoutBlock.merge_blocks([
            given_name_block, other_block, surname_block
        ])
        ref_text_block = LayoutBlock.merge_blocks([
            authors_block
        ])
        ref_block = LayoutBlock.merge_blocks([ref_text_block])
        fulltext_processor = FullTextProcessor(
            fulltext_models_mock,
            FullTextProcessorConfig(extract_citation_fields=True)
        )

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        reference_segmenter_model_mock = fulltext_models_mock.reference_segmenter_model_mock
        citation_model_mock = fulltext_models_mock.citation_model_mock
        name_citation_model_mock = fulltext_models_mock.name_citation_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            ref_block, '<references>'
        )

        reference_segmenter_model_mock.update_label_by_layout_block(
            ref_text_block, '<reference>'
        )

        citation_model_mock.update_label_by_layout_block(
            authors_block, '<author>'
        )

        name_citation_model_mock.update_label_by_layout_block(
            given_name_block, '<forename>'
        )
        name_citation_model_mock.update_label_by_layout_block(
            surname_block, '<surname>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            ref_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        LOGGER.debug('semantic_document: %s', semantic_document)
        assert semantic_document is not None
        reference_list = list(semantic_document.back_section.iter_by_type(SemanticReferenceList))
        assert len(reference_list) == 1
        references = list(reference_list[0].iter_by_type(SemanticReference))
        assert len(references) == 1
        ref = references[0]
        authors = list(ref.iter_by_type(SemanticAuthor))
        assert len(authors) == 1
        assert authors[0].given_name_text == given_name_block.text
        assert authors[0].surname_text == surname_block.text

    def test_should_extract_editor_names_from_references_fields(  # pylint: disable=too-many-locals
        self, fulltext_models_mock: MockFullTextModels
    ):
        given_name_block = LayoutBlock.for_text('Given name')
        surname_block = LayoutBlock.for_text('Surname')
        other_block = LayoutBlock.for_text('Other')
        editors_block = LayoutBlock.merge_blocks([
            given_name_block, other_block, surname_block
        ])
        ref_text_block = LayoutBlock.merge_blocks([
            editors_block
        ])
        ref_block = LayoutBlock.merge_blocks([ref_text_block])
        fulltext_processor = FullTextProcessor(
            fulltext_models_mock,
            FullTextProcessorConfig(
                extract_citation_fields=True,
                extract_citation_authors=False,
                extract_citation_editors=True
            )
        )

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        reference_segmenter_model_mock = fulltext_models_mock.reference_segmenter_model_mock
        citation_model_mock = fulltext_models_mock.citation_model_mock
        name_citation_model_mock = fulltext_models_mock.name_citation_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            ref_block, '<references>'
        )

        reference_segmenter_model_mock.update_label_by_layout_block(
            ref_text_block, '<reference>'
        )

        citation_model_mock.update_label_by_layout_block(
            editors_block, '<editor>'
        )

        name_citation_model_mock.update_label_by_layout_block(
            given_name_block, '<forename>'
        )
        name_citation_model_mock.update_label_by_layout_block(
            surname_block, '<surname>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            ref_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        LOGGER.debug('semantic_document: %s', semantic_document)
        assert semantic_document is not None
        reference_list = list(semantic_document.back_section.iter_by_type(SemanticReferenceList))
        assert len(reference_list) == 1
        references = list(reference_list[0].iter_by_type(SemanticReference))
        assert len(references) == 1
        ref = references[0]
        editors = list(ref.iter_by_type(SemanticEditor))
        assert len(editors) == 1
        assert editors[0].given_name_text == given_name_block.text
        assert editors[0].surname_text == surname_block.text

    @pytest.mark.parametrize(
        'segmentation_label',
        ['<body>', '<annex>']
    )
    def test_should_extract_figure_label_caption_from_body(  # pylint: disable=too-many-locals
        self, fulltext_models_mock: MockFullTextModels,
        segmentation_label: str
    ):
        citation_block = LayoutBlock.for_text('Figure 1')
        label_block = LayoutBlock.for_text('Figure 1')
        caption_block = LayoutBlock.for_text('Caption 1')
        other_block = LayoutBlock.for_text('Other')
        figure_block = LayoutBlock.merge_blocks([
            label_block, other_block, caption_block
        ])
        fulltext_block = LayoutBlock.merge_blocks([citation_block, figure_block])
        fulltext_processor = FullTextProcessor(
            fulltext_models_mock,
            FullTextProcessorConfig(extract_figure_fields=True)
        )

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        fulltext_model_mock = fulltext_models_mock.fulltext_model_mock
        figure_model_mock = fulltext_models_mock.figure_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            fulltext_block, segmentation_label
        )

        fulltext_model_mock.update_label_by_layout_block(
            citation_block, '<figure_marker>'
        )
        fulltext_model_mock.update_label_by_layout_block(
            figure_block, '<figure>'
        )

        figure_model_mock.update_label_by_layout_block(
            label_block, '<label>'
        )
        figure_model_mock.update_label_by_layout_block(
            caption_block, '<figDesc>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            fulltext_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        LOGGER.debug('semantic_document: %s', semantic_document)
        assert semantic_document is not None
        figure_list = list(iter_by_semantic_type_recursively(
            [semantic_document.body_section, semantic_document.back_section],
            SemanticFigure
        ))
        assert len(figure_list) == 1
        figure = figure_list[0]
        assert figure.get_text_by_type(SemanticLabel) == label_block.text
        assert figure.get_text_by_type(SemanticCaption) == caption_block.text
        assert figure.content_id == 'fig_0'
        figure_citation_list = list(
            semantic_document.iter_by_type_recursively(SemanticFigureCitation)
        )
        assert len(figure_citation_list) == 1
        assert figure_citation_list[0].get_text() == citation_block.text
        assert figure_citation_list[0].target_content_id == 'fig_0'

    @pytest.mark.parametrize(
        'segmentation_label',
        ['<body>', '<annex>']
    )
    def test_should_extract_table_label_caption_from_body(  # pylint: disable=too-many-locals
        self, fulltext_models_mock: MockFullTextModels,
        segmentation_label: str
    ):
        citation_block = LayoutBlock.for_text('Table 1')
        label_block = LayoutBlock.for_text('Table 1')
        caption_block = LayoutBlock.for_text('Caption 1')
        other_block = LayoutBlock.for_text('Other')
        figure_block = LayoutBlock.merge_blocks([
            label_block, other_block, caption_block
        ])
        fulltext_block = LayoutBlock.merge_blocks([citation_block, figure_block])
        fulltext_processor = FullTextProcessor(
            fulltext_models_mock,
            FullTextProcessorConfig(extract_table_fields=True)
        )

        segmentation_model_mock = fulltext_models_mock.segmentation_model_mock
        fulltext_model_mock = fulltext_models_mock.fulltext_model_mock
        table_model_mock = fulltext_models_mock.table_model_mock

        segmentation_model_mock.update_label_by_layout_block(
            fulltext_block, segmentation_label
        )

        fulltext_model_mock.update_label_by_layout_block(
            citation_block, '<table_marker>'
        )
        fulltext_model_mock.update_label_by_layout_block(
            figure_block, '<table>'
        )

        table_model_mock.update_label_by_layout_block(
            label_block, '<label>'
        )
        table_model_mock.update_label_by_layout_block(
            caption_block, '<figDesc>'
        )

        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            fulltext_block
        ])])
        semantic_document = fulltext_processor.get_semantic_document_for_layout_document(
            layout_document=layout_document
        )
        LOGGER.debug('semantic_document: %s', semantic_document)
        assert semantic_document is not None
        table_list = list(iter_by_semantic_type_recursively(
            [semantic_document.body_section, semantic_document.back_section],
            SemanticTable
        ))
        assert len(table_list) == 1
        table = table_list[0]
        assert table.get_text_by_type(SemanticLabel) == label_block.text
        assert table.get_text_by_type(SemanticCaption) == caption_block.text
        assert table.content_id == 'tab_0'
        table_citation_list = list(
            semantic_document.iter_by_type_recursively(SemanticTableCitation)
        )
        assert len(table_citation_list) == 1
        assert table_citation_list[0].get_text() == citation_block.text
        assert table_citation_list[0].target_content_id == 'tab_0'
