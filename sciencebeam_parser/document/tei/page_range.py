from lxml import etree

from sciencebeam_parser.document.semantic_document import (
    SemanticContentWrapper,
    SemanticPageRange,
)
from sciencebeam_parser.document.tei.common import (
    TEI_E
)
from sciencebeam_parser.document.tei.factory import (
    SingleElementTeiElementFactory,
    TeiElementFactoryContext
)


class TeiBiblScopeForPageRangeElementFactory(SingleElementTeiElementFactory):
    def get_tei_element_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> etree.ElementBase:
        assert isinstance(semantic_content, SemanticPageRange)
        page_range = semantic_content
        if not page_range.from_page or not page_range.to_page:
            return TEI_E(
                'biblScope',
                {'unit': 'page'},
                page_range.get_text()
            )
        return TEI_E(
            'biblScope',
            {
                'unit': 'page',
                'from': page_range.from_page,
                'to': page_range.to_page
            }
        )
