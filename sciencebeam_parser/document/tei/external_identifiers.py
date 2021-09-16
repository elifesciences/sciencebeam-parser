import logging

from lxml import etree

from sciencebeam_parser.document.semantic_document import (
    SemanticContentWrapper,
    SemanticExternalIdentifier
)
from sciencebeam_parser.document.tei.common import (
    TEI_E
)
from sciencebeam_parser.document.tei.factory import (
    SingleElementTeiElementFactory,
    TeiElementFactoryContext
)


LOGGER = logging.getLogger(__name__)


class ExternalIdentifierTeiElementFactory(SingleElementTeiElementFactory):
    def get_tei_element_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> etree.ElementBase:
        assert isinstance(semantic_content, SemanticExternalIdentifier)
        external_identifier = semantic_content
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug(
                'external_identifier: type=%r, value=%r, text=%r, content=%r',
                external_identifier.external_identifier_type,
                external_identifier.value,
                external_identifier.get_text(),
                external_identifier
            )
        attributes = context.get_default_attributes_for_semantic_content(external_identifier)
        if external_identifier.external_identifier_type:
            attributes = {**attributes, 'type': external_identifier.external_identifier_type}
        return TEI_E('idno', attributes, external_identifier.value)
