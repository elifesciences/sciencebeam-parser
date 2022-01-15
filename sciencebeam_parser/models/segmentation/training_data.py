import logging
from typing import Iterable, List, Tuple, Union

from lxml import etree
from lxml.builder import ElementMaker

from sciencebeam_parser.utils.xml_writer import XmlTreeWriter
from sciencebeam_parser.utils.xml import get_text_content
from sciencebeam_parser.utils.tokenizer import get_tokenized_tokens
from sciencebeam_parser.document.layout_document import (
    LayoutLine,
    LayoutToken,
    join_layout_tokens
)
from sciencebeam_parser.models.data import LayoutModelData
from sciencebeam_parser.models.model import (
    NEW_DOCUMENT_MARKER,
    NewDocumentMarker,
    get_split_prefix_label
)
from sciencebeam_parser.models.training_data import (
    AbstractTeiTrainingDataGenerator,
    get_model_data_label
)


LOGGER = logging.getLogger(__name__)


TEI_E = ElementMaker()


# based on:
# https://github.com/kermitt2/grobid/blob/0.7.0/grobid-core/src/main/java/org/grobid/core/engines/Segmentation.java
ROOT_TRAINING_XML_ELEMENT_PATH = ['text']
TRAINING_XML_ELEMENT_PATH_BY_LABEL = {
    '<other>': ROOT_TRAINING_XML_ELEMENT_PATH,
    'O': ROOT_TRAINING_XML_ELEMENT_PATH,
    '<header>': ROOT_TRAINING_XML_ELEMENT_PATH + ['front'],
    '<headnote>': ROOT_TRAINING_XML_ELEMENT_PATH + ['note[@place="headnote"]'],
    '<footnote>': ROOT_TRAINING_XML_ELEMENT_PATH + ['note[@place="footnote"]'],
    '<marginnote>': ROOT_TRAINING_XML_ELEMENT_PATH + ['note[@place="marginnote"]'],
    '<page>': ROOT_TRAINING_XML_ELEMENT_PATH + ['page'],
    '<references>': ROOT_TRAINING_XML_ELEMENT_PATH + ['listBibl'],
    '<body>': ROOT_TRAINING_XML_ELEMENT_PATH + ['body'],
    '<cover>': ROOT_TRAINING_XML_ELEMENT_PATH + ['titlePage'],
    '<toc>': ROOT_TRAINING_XML_ELEMENT_PATH + ['div[@type="toc"]'],
    '<annex>': ROOT_TRAINING_XML_ELEMENT_PATH + ['div[@type="annex"]'],
    '<acknowledgement>': ROOT_TRAINING_XML_ELEMENT_PATH + ['div[@type="acknowledgement"]'],
}


def iter_tokens_from_model_data(model_data: LayoutModelData) -> Iterable[LayoutToken]:
    if model_data.layout_token is not None:
        yield model_data.layout_token
        return
    assert model_data.layout_line is not None
    yield from model_data.layout_line.tokens


def iter_layout_lines_from_layout_tokens(
    layout_tokens: Iterable[LayoutToken]
) -> Iterable[LayoutLine]:
    line_layout_tokens: List[LayoutToken] = []
    for layout_token in layout_tokens:
        if not line_layout_tokens:
            line_layout_tokens.append(layout_token)
            continue
        if (
            layout_token.line_descriptor.line_id
            == line_layout_tokens[0].line_descriptor.line_id
        ):
            LOGGER.debug('line id matching: %r - %r', layout_token, line_layout_tokens[0])
            line_layout_tokens.append(layout_token)
            continue
        yield LayoutLine(tokens=line_layout_tokens)
        line_layout_tokens = [layout_token]
    if line_layout_tokens:
        yield LayoutLine(tokens=line_layout_tokens)


class SegmentationTeiTrainingDataGenerator(AbstractTeiTrainingDataGenerator):
    DEFAULT_TEI_FILENAME_SUFFIX = '.segmentation.tei.xml'
    DEFAULT_DATA_FILENAME_SUFFIX = '.segmentation'

    def __init__(self):
        super().__init__(
            root_training_xml_element_path=ROOT_TRAINING_XML_ELEMENT_PATH,
            training_xml_element_path_by_label=TRAINING_XML_ELEMENT_PATH_BY_LABEL,
            element_maker=TEI_E,
            default_tei_filename_suffix=(
                SegmentationTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
            ),
            default_data_filename_suffix=(
                SegmentationTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
            ),
            default_tei_sub_directory='segmentation/corpus/tei',
            default_data_sub_directory='segmentation/corpus/raw'
        )

    def write_xml_line_for_layout_tokens(
        self,
        xml_writer: XmlTreeWriter,
        layout_tokens: Iterable[LayoutToken]
    ):
        xml_writer.append_text(join_layout_tokens(layout_tokens))
        xml_writer.append(TEI_E('lb'))

    def write_xml_for_model_data_iterable(
        self,
        xml_writer: XmlTreeWriter,
        model_data_iterable: Iterable[LayoutModelData]
    ):
        default_path = xml_writer.current_path
        pending_whitespace = ''
        for model_data in model_data_iterable:
            prefixed_label = get_model_data_label(model_data)
            _prefix, label = get_split_prefix_label(prefixed_label or '')
            xml_element_path = self.get_training_xml_path_for_label(
                label,
                current_path=xml_writer.current_path
            )
            LOGGER.debug('label: %r (%r)', label, xml_element_path)
            if xml_writer.current_path != xml_element_path:
                xml_writer.require_path(default_path)
            xml_writer.append_text(pending_whitespace)
            pending_whitespace = ''
            xml_writer.require_path(xml_element_path)
            for layout_line in iter_layout_lines_from_layout_tokens(
                iter_tokens_from_model_data(model_data)
            ):
                self.write_xml_line_for_layout_tokens(
                    xml_writer,
                    layout_line.tokens
                )
                pending_whitespace = '\n'
        xml_writer.require_path(default_path)
        xml_writer.append_text(pending_whitespace)


def iter_tag_result_for_flat_tag_result(
    flat_tag_result_iterable: Iterable[Union[Tuple[str, str], NewDocumentMarker]]
) -> Iterable[List[Tuple[str, str]]]:
    doc_tag_result: List[Tuple[str, str]] = []
    for token_tag_result in flat_tag_result_iterable:
        if isinstance(token_tag_result, NewDocumentMarker):
            yield doc_tag_result
            doc_tag_result = []
            continue
        doc_tag_result.append(token_tag_result)


def get_tag_result_for_flat_tag_result(
    flat_tag_result_iterable: Iterable[Union[Tuple[str, str], NewDocumentMarker]]
) -> List[List[Tuple[str, str]]]:
    return list(iter_tag_result_for_flat_tag_result(flat_tag_result_iterable))


class SegmentationTrainingTeiParser:
    def iter_parse_training_tei_to_flat_tag_result(
        self,
        tei_root: etree.ElementBase
    ) -> Iterable[Union[Tuple[str, str], NewDocumentMarker]]:
        for text_node in tei_root.xpath('./text'):
            if text_node.text:
                for token_text in get_tokenized_tokens(text_node.text):
                    yield token_text, 'O'
            for child_node in text_node:
                label = '<' + child_node.tag + '>'
                for token_index, token_text in enumerate(
                    get_tokenized_tokens(get_text_content(child_node))
                ):
                    prefix = 'B-' if token_index == 0 else 'I-'
                    yield token_text, prefix + label
            yield NEW_DOCUMENT_MARKER

    def parse_training_tei_to_tag_result(
        self,
        tei_root: etree.ElementBase
    ):
        return get_tag_result_for_flat_tag_result(
            self.iter_parse_training_tei_to_flat_tag_result(
                tei_root
            )
        )
