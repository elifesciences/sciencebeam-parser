import logging
from typing import Iterable, Mapping, Optional, Tuple

from pygrobid.utils.misc import iter_ids
from pygrobid.document.semantic_document import (
    SemanticAddressLine,
    SemanticAffiliationAddress,
    SemanticContentFactoryProtocol,
    SemanticContentWrapper,
    SemanticCountry,
    SemanticDepartment,
    SemanticInstitution,
    SemanticLaboratory,
    SemanticMarker,
    SemanticNote,
    SemanticPostBox,
    SemanticPostCode,
    SemanticRegion,
    SemanticSettlement
)
from pygrobid.document.layout_document import LayoutBlock
from pygrobid.models.extract import SimpleModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG: Mapping[str, SemanticContentFactoryProtocol] = {
    '<institution>': SemanticInstitution,
    '<department>': SemanticDepartment,
    '<laboratory>': SemanticLaboratory,
    '<addrLine>': SemanticAddressLine,
    '<postCode>': SemanticPostCode,
    '<postBox>': SemanticPostBox,
    '<region>': SemanticRegion,
    '<settlement>': SemanticSettlement,
    '<country>': SemanticCountry
}


class AffiliationAddressSemanticExtractor(SimpleModelSemanticExtractor):
    def __init__(self):
        super().__init__(semantic_content_class_by_tag=SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG)

    def iter_semantic_content_for_entity_blocks(
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        **kwargs
    ) -> Iterable[SemanticContentWrapper]:
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        ids_iterator = iter(iter_ids('aff'))
        aff: Optional[SemanticAffiliationAddress] = None
        for name, layout_block in entity_tokens:
            if name == '<marker>':
                if aff:
                    yield aff
                aff = SemanticAffiliationAddress(content_id=next(ids_iterator, '?'))
                aff.add_content(SemanticMarker(layout_block=layout_block))
                continue
            semantic_content = self.get_semantic_content_for_entity_name(
                name, layout_block
            )
            if not aff:
                if isinstance(semantic_content, SemanticNote):
                    yield semantic_content
                    continue
                aff = SemanticAffiliationAddress(content_id=next(ids_iterator, '?'))
            aff.add_content(semantic_content)
        if aff:
            yield aff
