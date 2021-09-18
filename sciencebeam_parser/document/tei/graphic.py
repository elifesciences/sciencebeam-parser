import logging

from lxml import etree

from sciencebeam_parser.document.semantic_document import (
    SemanticContentWrapper,
    SemanticGraphic,
)
from sciencebeam_parser.document.tei.common import (
    TEI_E,
    format_coordinates
)
from sciencebeam_parser.document.tei.factory import (
    SingleElementTeiElementFactory,
    TeiElementFactoryContext
)


LOGGER = logging.getLogger(__name__)


class GraphicTeiElementFactory(SingleElementTeiElementFactory):
    def get_tei_element_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> etree.ElementBase:
        LOGGER.debug('semantic_content: %s', semantic_content)
        assert isinstance(semantic_content, SemanticGraphic)
        semantic_graphic = semantic_content
        layout_graphic = semantic_graphic.layout_graphic
        children = [
            context.get_default_attributes_for_semantic_content(
                semantic_graphic,
                enable_coordinates=False
            )
        ]
        if semantic_graphic.relative_path:
            children.append({'url': semantic_graphic.relative_path})
        if layout_graphic:
            if layout_graphic.coordinates:
                children.append({'coords': format_coordinates(layout_graphic.coordinates)})
            if layout_graphic.graphic_type:
                children.append({'type': layout_graphic.graphic_type})
        return TEI_E('graphic', *children)
