import logging
from typing import Iterable, List, Optional, Union

from lxml import etree
from lxml.builder import ElementMaker

from sciencebeam_parser.utils.xml_writer import XmlTreeWriter
from sciencebeam_parser.document.layout_document import (
    LayoutDocument,
    LayoutLine,
    LayoutToken,
    join_layout_tokens
)
from sciencebeam_parser.models.data import LabeledLayoutModelData, LayoutModelData


LOGGER = logging.getLogger(__name__)


TEI_E = ElementMaker()


TRAINING_XML_ELEMENT_PATH_BY_LABEL = {
    '<front>': ['text', 'front'],
    '<body>': ['text', 'body']
}


def iter_tokens_from_model_data(model_data: LayoutModelData) -> Iterable[LayoutToken]:
    if model_data.layout_token is not None:
        yield model_data.layout_token
        return
    assert model_data.layout_line is not None
    yield from model_data.layout_line.tokens


def get_model_data_label(model_data: LayoutModelData) -> Optional[str]:
    if isinstance(model_data, LabeledLayoutModelData):
        return model_data.label
    return None


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


class SegmentationTeiTrainingDataGenerator:
    DEFAULT_TEI_FILENAME_SUFFIX = '.segmentation.tei.xml'
    DEFAULT_DATA_FILENAME_SUFFIX = '.segmentation'

    def iter_training_tei_children_for_line_layout_tokens(
        self,
        layout_tokens: Iterable[LayoutToken]
    ) -> Iterable[Union[str, etree.ElementBase]]:
        yield join_layout_tokens(layout_tokens)
        yield TEI_E('lb')
        yield '\n'

    def iter_training_tei_children_for_line_layout_lines(
        self,
        layout_lines: Iterable[LayoutLine]
    ) -> Iterable[Union[str, etree.ElementBase]]:
        for layout_line in layout_lines:
            yield from self.iter_training_tei_children_for_line_layout_tokens(
                layout_line.tokens
            )

    def iter_tei_child_for_model_data_iterable(
        self,
        model_data_iterable: Iterable[LayoutModelData]
    ) -> Iterable[Union[str, etree.ElementBase]]:
        yield from self.iter_training_tei_children_for_line_layout_lines((
            layout_line
            for model_data in model_data_iterable
            for layout_line in iter_layout_lines_from_layout_tokens(
                iter_tokens_from_model_data(model_data)
            )
        ))

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
        pending_text = ''
        for model_data in model_data_iterable:
            label = get_model_data_label(model_data)
            xml_element_path = TRAINING_XML_ELEMENT_PATH_BY_LABEL.get(label or '', default_path)
            if xml_writer.current_path != xml_element_path:
                xml_writer.require_path(default_path)
            xml_writer.append_text(pending_text)
            pending_text = ''
            xml_writer.require_path(xml_element_path)
            for layout_line in iter_layout_lines_from_layout_tokens(
                iter_tokens_from_model_data(model_data)
            ):
                self.write_xml_line_for_layout_tokens(
                    xml_writer,
                    layout_line.tokens
                )
                pending_text = '\n'
        xml_writer.require_path(default_path)
        xml_writer.append_text(pending_text)

    def _get_training_tei_xml_for_children(
        self,
        children: Iterable[Union[str, etree.ElementBase]]
    ) -> etree.ElementBase:
        return TEI_E(
            'tei',
            TEI_E(
                'text',
                *list(children)
            )
        )

    def _get_xml_writer(self) -> XmlTreeWriter:
        return XmlTreeWriter(
            TEI_E('tei'),
            element_maker=TEI_E
        )

    def get_training_tei_xml_for_model_data_iterable(
        self,
        model_data_iterable: Iterable[LayoutModelData]
    ) -> etree.ElementBase:
        xml_writer = self._get_xml_writer()
        xml_writer.require_path(['text'])
        self.write_xml_for_model_data_iterable(
            xml_writer,
            model_data_iterable=model_data_iterable
        )
        return xml_writer.root

    def get_training_tei_xml_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> etree.ElementBase:
        return self._get_training_tei_xml_for_children(
            self.iter_training_tei_children_for_line_layout_lines(
                layout_document.iter_all_lines()
            )
        )
