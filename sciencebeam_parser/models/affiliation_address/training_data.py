import logging
from typing import Iterable, List, Optional, Sequence

from lxml import etree

from sciencebeam_parser.utils.xml_writer import XmlTreeWriter
from sciencebeam_parser.document.layout_document import (
    LayoutLine,
    LayoutToken,
    join_layout_tokens
)
from sciencebeam_parser.document.tei.common import TEI_E
from sciencebeam_parser.models.model import get_split_prefix_label
from sciencebeam_parser.models.data import LabeledLayoutModelData, LayoutModelData


LOGGER = logging.getLogger(__name__)


# based on:
# https://github.com/kermitt2/grobid/blob/0.7.0/grobid-core/src/main/java/org/grobid/core/engines/AffiliationAddressParser.java
ROOT_TRAINING_XML_ELEMENT_PATH = [
    'teiHeader', 'fileDesc', 'sourceDesc', 'biblStruct', 'analytic', 'author',
    'affiliation'
]

OTHER_LABELS = {'<other>', 'O'}

TRAINING_XML_ELEMENT_PATH_BY_LABEL = {
    '<marker>': ROOT_TRAINING_XML_ELEMENT_PATH + ['marker'],
    '<institution>': ROOT_TRAINING_XML_ELEMENT_PATH + ['orgName[@type="institution"]'],
    '<department>': ROOT_TRAINING_XML_ELEMENT_PATH + ['orgName[@type="department"]'],
    '<laboratory>': ROOT_TRAINING_XML_ELEMENT_PATH + ['orgName[@type="laboratory"]'],
    '<addrLine>': ROOT_TRAINING_XML_ELEMENT_PATH + ['address', 'addrLine'],
    '<postCode>': ROOT_TRAINING_XML_ELEMENT_PATH + ['address', 'postCode'],
    '<postBox>': ROOT_TRAINING_XML_ELEMENT_PATH + ['address', 'postBox'],
    '<region>': ROOT_TRAINING_XML_ELEMENT_PATH + ['address', 'region'],
    '<settlement>': ROOT_TRAINING_XML_ELEMENT_PATH + ['address', 'settlement'],
    '<country>': ROOT_TRAINING_XML_ELEMENT_PATH + ['address', 'country']
}

TRAINING_XML_ELEMENT_PATHS = {
    tuple(value)
    for value in TRAINING_XML_ELEMENT_PATH_BY_LABEL.values()
}


def get_model_data_label(model_data: LayoutModelData) -> Optional[str]:
    if isinstance(model_data, LabeledLayoutModelData):
        return model_data.label
    return None


def is_same_layout_line(
    layout_line_1: Optional[LayoutLine],
    layout_line_2: Optional[LayoutLine]
) -> bool:
    assert layout_line_1 is not None
    assert layout_line_2 is not None
    return id(layout_line_1) == id(layout_line_2)


def is_same_model_data_layout_line(
    model_data_1: LayoutModelData,
    model_data_2: LayoutModelData
) -> bool:
    return is_same_layout_line(model_data_1.layout_line, model_data_2.layout_line)


def iter_group_model_data_by_line(
    model_data_iterable: Iterable[LayoutModelData]
) -> Iterable[Sequence[LayoutModelData]]:
    line_model_data_list: List[LayoutModelData] = []
    for model_data in model_data_iterable:
        if not line_model_data_list:
            line_model_data_list.append(model_data)
            continue
        previous_model_data = line_model_data_list[-1]
        if is_same_model_data_layout_line(
            model_data,
            previous_model_data
        ):
            LOGGER.debug('same line: %r - %r', model_data, previous_model_data)
            line_model_data_list.append(model_data)
            continue
        yield line_model_data_list
        line_model_data_list = [model_data]
    if line_model_data_list:
        yield line_model_data_list


def get_default_note_type_for_label(label: str) -> str:
    return label.strip('<>')


def get_training_xml_path_for_label(
    label: Optional[str],
    current_path: Sequence[str]
) -> Sequence[str]:
    if not label or label in OTHER_LABELS:
        if tuple(current_path) in TRAINING_XML_ELEMENT_PATHS:
            return current_path[:-1]
        return current_path
    training_xml_path = TRAINING_XML_ELEMENT_PATH_BY_LABEL.get(label or '')
    if not training_xml_path:
        note_type = get_default_note_type_for_label(label)
        LOGGER.info('label not mapped, creating note: %r', label)
        training_xml_path = ROOT_TRAINING_XML_ELEMENT_PATH + [f'note[@type="{note_type}"]']
    return training_xml_path


class AffiliationAddressTeiTrainingDataGenerator:
    DEFAULT_TEI_FILENAME_SUFFIX = '.affiliation.tei.xml'
    DEFAULT_DATA_FILENAME_SUFFIX = '.affiliation'

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
        prev_label: str = ''
        for line_model_data_list in iter_group_model_data_by_line(model_data_iterable):
            for model_data in line_model_data_list:
                layout_token = model_data.layout_token
                assert layout_token is not None
                prefixed_label = get_model_data_label(model_data)
                prefix, label = get_split_prefix_label(prefixed_label or '')
                xml_element_path = get_training_xml_path_for_label(
                    label,
                    current_path=xml_writer.current_path
                )
                LOGGER.debug('label: %r (%r: %r)', label, prefix, xml_element_path)
                if (
                    prev_label not in OTHER_LABELS
                    and pending_whitespace
                    and xml_writer.current_path != xml_element_path
                ):
                    xml_writer.require_path(xml_writer.current_path[:-1])
                elif prefix == 'B' and label not in OTHER_LABELS:
                    xml_writer.require_path(xml_element_path[:-1])
                xml_writer.append_text(pending_whitespace)
                pending_whitespace = ''
                xml_writer.require_path(xml_element_path)
                xml_writer.append_text(layout_token.text)
                pending_whitespace = layout_token.whitespace
                prev_label = label
            xml_writer.append(TEI_E('lb'))
            pending_whitespace = '\n'
        xml_writer.require_path(default_path)
        xml_writer.append_text(pending_whitespace)

    def _get_xml_writer(self) -> XmlTreeWriter:
        return XmlTreeWriter(
            TEI_E('tei'),
            element_maker=TEI_E
        )

    def get_training_tei_xml_for_multiple_model_data_iterables(
        self,
        model_data_iterables: Iterable[Iterable[LayoutModelData]]
    ) -> etree.ElementBase:
        xml_writer = self._get_xml_writer()
        xml_writer.require_path(ROOT_TRAINING_XML_ELEMENT_PATH[:-1])
        for model_data_iterable in model_data_iterables:
            xml_writer.require_path(ROOT_TRAINING_XML_ELEMENT_PATH[:-1])
            xml_writer.require_path(ROOT_TRAINING_XML_ELEMENT_PATH)
            self.write_xml_for_model_data_iterable(
                xml_writer,
                model_data_iterable=model_data_iterable
            )
        return xml_writer.root

    def get_training_tei_xml_for_model_data_iterable(
        self,
        model_data_iterable: Iterable[LayoutModelData]
    ) -> etree.ElementBase:
        return self.get_training_tei_xml_for_multiple_model_data_iterables(
            [model_data_iterable]
        )
