import logging

from lxml import etree

from sciencebeam_parser.document.semantic_document import (
    SemanticContentWrapper,
    SemanticMixedNote
)
from sciencebeam_parser.document.tei.common import (
    TEI_E
)
from sciencebeam_parser.document.tei.factory import (
    SingleElementTeiElementFactory,
    TeiElementFactoryContext
)


LOGGER = logging.getLogger(__name__)


class SemanticMixedNoteTeiElementFactory(SingleElementTeiElementFactory):
    def get_tei_element_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> etree.ElementBase:
        LOGGER.debug('semantic_content: %s', semantic_content)
        assert isinstance(semantic_content, SemanticMixedNote)
        semantic_mixed_note = semantic_content
        note_type = semantic_mixed_note.note_type or 'other'
        children = [context.get_default_attributes_for_semantic_content(semantic_mixed_note)]
        children.append({'type': note_type})
        for child_semantic_content in semantic_mixed_note:
            children.extend(context.get_tei_child_elements_for_semantic_content(
                child_semantic_content
            ))
        return TEI_E('note', *children)
