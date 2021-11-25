from lxml import etree
from lxml.builder import ElementMaker

from sciencebeam_parser.document.layout_document import LayoutDocument


TEI_E = ElementMaker()


class SegmentationTeiTrainingDataGenerator:
    def get_training_tei_xml_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> etree.ElementBase:
        return TEI_E.tei(
            TEI_E.text('\n'.join([
                block.text
                for block in layout_document.iter_all_blocks()
            ]))
        )
