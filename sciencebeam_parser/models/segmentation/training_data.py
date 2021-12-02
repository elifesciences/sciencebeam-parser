import logging
from typing import Iterable, List, Union

from lxml import etree
from lxml.builder import ElementMaker

from sciencebeam_parser.document.layout_document import (
    LayoutDocument,
    LayoutLine,
    LayoutToken,
    join_layout_tokens
)
from sciencebeam_parser.models.data import LayoutModelData


LOGGER = logging.getLogger(__name__)


TEI_E = ElementMaker()


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

    def get_training_tei_xml_for_model_data_iterable(
        self,
        model_data_iterable: Iterable[LayoutModelData]
    ) -> etree.ElementBase:
        return self._get_training_tei_xml_for_children(
            self.iter_tei_child_for_model_data_iterable(model_data_iterable)
        )

    def get_training_tei_xml_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> etree.ElementBase:
        return self._get_training_tei_xml_for_children(
            self.iter_training_tei_children_for_line_layout_lines(
                layout_document.iter_all_lines()
            )
        )
