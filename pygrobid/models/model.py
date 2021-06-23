import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from sciencebeam_trainer_delft.sequence_labelling.reader import load_data_crf_lines

from pygrobid.document.layout_document import (
    LayoutToken,
    LayoutLine,
    LayoutBlock,
    LayoutPage,
    LayoutDocument
)
from pygrobid.models.data import ModelDataGenerator
from pygrobid.models.extract import ModelSemanticExtractor
from pygrobid.document.semantic_document import SemanticContentWrapper


LOGGER = logging.getLogger(__name__)


@dataclass
class LayoutModelLabel:
    label: str
    label_token_text: str
    layout_line: Optional[LayoutLine] = None
    layout_token: Optional[LayoutToken] = None


def strip_tag_prefix(tag: str) -> str:
    if tag and (tag.startswith('B-') or tag.startswith('I-')):
        return tag[2:]
    return tag


class LayoutDocumentLabelResult:
    def __init__(
        self,
        layout_document: LayoutDocument,
        layout_model_label_iterable: Iterable[LayoutModelLabel]
    ):
        self.layout_document = layout_document
        self.layout_model_label_list = list(layout_model_label_iterable)
        self.layout_document_labels_by_label: Dict[str, List[LayoutModelLabel]] = (
            defaultdict(list)
        )
        for layout_model_label in self.layout_model_label_list:
            tag_without_prefix = strip_tag_prefix(layout_model_label.label)
            self.layout_document_labels_by_label[tag_without_prefix].append(
                layout_model_label
            )

    def get_available_labels(self) -> Set[str]:
        return set(self.layout_document_labels_by_label.keys())

    def get_layout_document_labels_by_labels(self, labels: List[str]) -> List[LayoutModelLabel]:
        if not labels:
            return []
        if len(labels) == 1:
            return self.layout_document_labels_by_label.get(labels[0], [])
        result: List[LayoutModelLabel] = []
        for label in labels:
            result.extend(self.layout_document_labels_by_label.get(label, []))
        return result

    def get_filtered_document_by_label(self, label: str) -> LayoutDocument:
        return self.get_filtered_document_by_labels([label])

    def get_filtered_document_by_labels(
        self,
        labels: List[str]
    ):  # pylint: disable=too-many-branches
        layout_document = LayoutDocument(pages=[])
        layout_document_labels = self.get_layout_document_labels_by_labels(labels)
        if not layout_document_labels:
            LOGGER.warning(
                'no layout_lines_to_include found for: %r, available keys=%r',
                labels, self.layout_document_labels_by_label.keys()
            )
            return layout_document
        layout_token_ids_to_include = {
            id(layout_document_label.layout_token)
            for layout_document_label in layout_document_labels
            if layout_document_label.layout_token
        }
        LOGGER.debug('layout_tokens_to_include: %s', layout_token_ids_to_include)
        layout_line_ids_to_include: Set[int] = set()
        if not layout_token_ids_to_include:
            layout_line_ids_to_include = {
                id(layout_document_label.layout_line)
                for layout_document_label in layout_document_labels
                if layout_document_label.layout_line
            }
        LOGGER.debug('layout_line_ids_to_include: %s', layout_line_ids_to_include)
        result_page: Optional[LayoutPage] = None
        for page in self.layout_document.pages:  # pylint: disable=too-many-nested-blocks
            result_page = None
            result_block: Optional[LayoutBlock] = None
            for block in page.blocks:
                result_block = None
                for line in block.lines:
                    accepted_line: Optional[LayoutLine] = None
                    if layout_token_ids_to_include:
                        accepted_tokens: List[LayoutToken] = []
                        for token in line.tokens:
                            if id(token) in layout_token_ids_to_include:
                                accepted_tokens.append(token)
                        if not accepted_tokens:
                            continue
                        if len(line.tokens) == accepted_tokens:
                            accepted_line = line
                        else:
                            accepted_line = LayoutLine(tokens=accepted_tokens)
                    else:
                        if id(line) not in layout_line_ids_to_include:
                            continue
                        accepted_line = line
                    if result_page is None:
                        result_page = LayoutPage(blocks=[])
                        layout_document.pages.append(result_page)
                    if result_block is None:
                        result_block = LayoutBlock(lines=[])
                        result_page.blocks.append(result_block)
                    result_block.lines.append(accepted_line)
        return layout_document


class Model(ABC):
    @abstractmethod
    def get_data_generator(self) -> ModelDataGenerator:
        pass

    # @abstractmethod
    def get_semantic_extractor(self) -> ModelSemanticExtractor:
        raise NotImplementedError()

    def iter_semantic_content_for_entity_blocks(
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]]
    ) -> Iterable[SemanticContentWrapper]:
        return self.get_semantic_extractor().iter_semantic_content_for_entity_blocks(
            entity_tokens
        )

    @abstractmethod
    def predict_labels(
        self,
        texts: List[List[str]],
        features: List[List[List[str]]],
        output_format: Optional[str] = None
    ) -> List[List[Tuple[str, str]]]:
        pass

    def iter_label_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> Iterable[LayoutModelLabel]:
        data_generator = self.get_data_generator()
        model_data_iterable = list(data_generator.iter_model_data_for_layout_document(
            layout_document
        ))
        data_lines = (model_data.data_line for model_data in model_data_iterable)
        texts, features = load_data_crf_lines(data_lines)
        texts = texts.tolist()
        tag_result = self.predict_labels(
            texts=texts, features=features, output_format=None
        )
        if not tag_result:
            return
        first_doc_tag_result = tag_result[0]
        if len(first_doc_tag_result) != len(model_data_iterable):
            raise AssertionError('tag result does not match data: %d != %d' % (
                len(first_doc_tag_result), len(model_data_iterable)
            ))
        for token_tag_result, token_model_data in zip(first_doc_tag_result, model_data_iterable):
            label_token_text, token_label = token_tag_result
            if label_token_text != token_model_data.label_token_text:
                raise AssertionError(
                    f'actual: {repr(label_token_text)}'
                    f', expected: {repr(token_model_data.label_token_text)}'
                )
            yield LayoutModelLabel(
                label=token_label,
                label_token_text=label_token_text,
                layout_line=token_model_data.layout_line,
                layout_token=token_model_data.layout_token
            )

    def get_label_layout_document_result(
        self,
        layout_document: LayoutDocument
    ) -> LayoutDocumentLabelResult:
        return LayoutDocumentLabelResult(
            layout_document=layout_document,
            layout_model_label_iterable=self.iter_label_layout_document(layout_document)
        )
