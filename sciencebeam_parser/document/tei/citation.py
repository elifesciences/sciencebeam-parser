from typing import (
    Any,
    Mapping,
    Type
)

from lxml import etree

from sciencebeam_parser.document.semantic_document import (
    SemanticCitation,
    SemanticContentWrapper,
    SemanticFigureCitation,
    SemanticReferenceCitation,
    SemanticTableCitation
)
from sciencebeam_parser.document.tei.common import (
    TEI_E
)
from sciencebeam_parser.document.tei.factory import (
    SingleElementTeiElementFactory,
    TeiElementFactoryContext
)


CITATION_TYPE_BY_SEMANTIC_CLASS: Mapping[Type[Any], str] = {
    SemanticFigureCitation: 'figure',
    SemanticTableCitation: 'table',
    SemanticReferenceCitation: 'bibr'
}


class CitationTeiElementFactory(SingleElementTeiElementFactory):
    def get_tei_element_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> etree.ElementBase:
        assert isinstance(semantic_content, SemanticCitation)
        citation = semantic_content
        citation_type = CITATION_TYPE_BY_SEMANTIC_CLASS.get(type(citation))
        attributes = {}
        if citation_type:
            attributes['type'] = citation_type
        if citation.target_content_id:
            attributes['target'] = '#' + citation.target_content_id
        return TEI_E(
            'ref',
            attributes,
            *context.iter_layout_block_tei_children(citation.merged_block)
        )
