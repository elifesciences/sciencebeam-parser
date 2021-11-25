from typing import Iterable, Union
from lxml import etree
from lxml.builder import ElementMaker

from sciencebeam_parser.document.layout_document import LayoutDocument, LayoutLine


TEI_E = ElementMaker()


class SegmentationTeiTrainingDataGenerator:
    def get_training_tei_children_for_layout_line(
        self,
        layout_line: LayoutLine
    ) -> Iterable[Union[str, etree.ElementBase]]:
        yield layout_line.text
        yield TEI_E.lb()
        yield '\n'

    def get_training_tei_xml_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> etree.ElementBase:
        return TEI_E.tei(
            TEI_E.text(*[
                child
                for block in layout_document.iter_all_blocks()
                for line in block.lines
                for child in self.get_training_tei_children_for_layout_line(line)
            ])
        )
