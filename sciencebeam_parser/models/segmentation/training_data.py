import logging
from typing import Iterable, List, NamedTuple, Sequence, Tuple, Union

from lxml import etree
from lxml.builder import ElementMaker

from sciencebeam_parser.utils.xml_writer import XmlTreeWriter
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
    OTHER_LABELS,
    AbstractTeiTrainingDataGenerator,
    ExtractInstruction,
    NewLineExtractInstruction,
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


TEI_LB = 'lb'


def _get_tag_expression_for_element(element: etree.ElementBase) -> str:
    if not element.attrib:
        return element.tag
    if len(element.attrib) > 1:
        raise ValueError('only supporting up to one attribute')
    key, value = list(element.attrib.items())[0]
    return '{tag}[@{key}="{value}"]'.format(tag=element.tag, key=key, value=value)


class TeiTrainingElementPath(NamedTuple):
    element_list: Sequence[etree.ElementBase] = tuple([])

    def get_path(self) -> Sequence[str]:
        return [
            _get_tag_expression_for_element(element)
            for element in self.element_list
        ]

    def append(self, element: etree.ElementBase) -> 'TeiTrainingElementPath':
        return TeiTrainingElementPath(
            list(self.element_list) + [element]
        )


EMPTY_TEI_TRAINING_ELEMENT_PATH = TeiTrainingElementPath()


class TeiTrainingText(NamedTuple):
    text: str
    path: TeiTrainingElementPath


class TeiTrainingLine(NamedTuple):
    text_list: Sequence[TeiTrainingText]


def _iter_flat_tei_training_text_from_element(
    parent_element: etree.ElementBase,
    current_path: TeiTrainingElementPath = EMPTY_TEI_TRAINING_ELEMENT_PATH
) -> Iterable[Union[TeiTrainingText, ExtractInstruction]]:
    LOGGER.debug('current_path: %s', current_path)
    if parent_element.text:
        yield TeiTrainingText(
            text=parent_element.text,
            path=current_path
        )

    for child_element in parent_element:
        if child_element.tag == TEI_LB:
            yield NewLineExtractInstruction()
        else:
            child_path = current_path.append(child_element)
            yield from _iter_flat_tei_training_text_from_element(
                child_element,
                child_path
            )

        if child_element.tail:
            yield TeiTrainingText(
                text=child_element.tail,
                path=current_path
            )


def _iter_tei_training_lines_from_element(
    parent_element: etree.ElementBase,
    current_path: TeiTrainingElementPath = EMPTY_TEI_TRAINING_ELEMENT_PATH
) -> Iterable[TeiTrainingLine]:
    line_text_list = []
    for item in _iter_flat_tei_training_text_from_element(
        parent_element,
        current_path
    ):
        if isinstance(item, TeiTrainingText):
            line_text_list.append(item)
        elif isinstance(item, NewLineExtractInstruction):
            yield TeiTrainingLine(line_text_list)
            line_text_list = []
        else:
            raise RuntimeError('unrecognised item: %r' % item)
    if line_text_list:
        yield TeiTrainingLine(line_text_list)


class SegmentationTrainingTeiParser:
    def __init__(self) -> None:
        self.label_by_relative_element_path_map = {
            tuple(element_path[len(ROOT_TRAINING_XML_ELEMENT_PATH):]): label
            for label, element_path in TRAINING_XML_ELEMENT_PATH_BY_LABEL.items()
        }

    def _get_label_for_element_path(
        self,
        tei_training_element_path: TeiTrainingElementPath
    ) -> str:
        element_path = tei_training_element_path.get_path()
        label = self.label_by_relative_element_path_map.get(tuple(element_path))
        if not label:
            raise RuntimeError('label not found for %r' % element_path)
        return label

    def iter_parse_training_tei_to_flat_tag_result(
        self,
        tei_root: etree.ElementBase
    ) -> Iterable[Union[Tuple[str, str], NewDocumentMarker]]:
        for text_node in tei_root.xpath('./text'):
            tei_training_lines = list(
                _iter_tei_training_lines_from_element(
                    text_node, EMPTY_TEI_TRAINING_ELEMENT_PATH
                )
            )
            LOGGER.debug('tei_training_lines: %r', tei_training_lines)
            prefix = ''
            prev_label = ''
            for line in tei_training_lines:
                for text in line.text_list:
                    token_count = 0
                    if text.path.element_list:
                        label = self._get_label_for_element_path(text.path)
                        if prev_label != label:
                            prefix = 'B-'
                    else:
                        label = 'O'
                        prefix = ''
                    if label in OTHER_LABELS:
                        prefix = ''
                    prev_label = label
                    for token_text in get_tokenized_tokens(text.text):
                        yield token_text, prefix + label
                        token_count += 1
                        if prefix:
                            prefix = 'I-'
                        break
                    if token_count:
                        # we are only outputting the first token of each line
                        break
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
