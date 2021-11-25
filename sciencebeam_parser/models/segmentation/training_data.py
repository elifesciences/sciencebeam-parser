import logging
from typing import Iterable, List, Union

from lxml import etree
from lxml.builder import ElementMaker

from sciencebeam_parser.document.layout_document import (
    LayoutDocument,
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


class SegmentationTeiTrainingDataGenerator:
    def iter_training_tei_children_for_line_layout_tokens(
        self,
        layout_tokens: Iterable[LayoutToken]
    ) -> Iterable[Union[str, etree.ElementBase]]:
        yield join_layout_tokens(layout_tokens)
        yield TEI_E.lb()
        yield '\n'

    def iter_tei_child_for_tokens(
        self,
        layout_tokens: Iterable[LayoutToken]
    ) -> Iterable[Union[str, etree.ElementBase]]:
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
            yield from self.iter_training_tei_children_for_line_layout_tokens(
                line_layout_tokens
            )
            line_layout_tokens.clear()
            line_layout_tokens.append(layout_token)
        if line_layout_tokens:
            yield from self.iter_training_tei_children_for_line_layout_tokens(
                line_layout_tokens
            )

    def iter_tei_child_for_model_data_iterable(
        self,
        model_data_iterable: Iterable[LayoutModelData]
    ) -> Iterable[Union[str, etree.ElementBase]]:
        yield from self.iter_tei_child_for_tokens((
            layout_token
            for model_data in model_data_iterable
            for layout_token in iter_tokens_from_model_data(model_data)
        ))

    def get_training_tei_xml_for_model_data_iterable(
        self,
        model_data_iterable: Iterable[LayoutModelData]
    ) -> etree.ElementBase:
        return TEI_E.tei(
            TEI_E.text(*list(
                self.iter_tei_child_for_model_data_iterable(model_data_iterable)
            ))
        )

    def get_training_tei_xml_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> etree.ElementBase:
        return TEI_E.tei(
            TEI_E.text(*[
                child
                for block in layout_document.iter_all_blocks()
                for line in block.lines
                for child in self.iter_training_tei_children_for_line_layout_tokens(
                    line.tokens
                )
            ])
        )
