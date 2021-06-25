import logging
from typing import Iterable, Optional, Tuple

from pygrobid.utils.misc import iter_ids
from pygrobid.document.semantic_document import (
    SemanticAddressLine,
    SemanticAffiliationAddress,
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
from pygrobid.models.extract import ModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


class AffiliationAddressSemanticExtractor(ModelSemanticExtractor):
    def get_semantic_content_for_entity_name(  # pylint: disable=too-many-return-statements
        self,
        name: str,
        layout_block: LayoutBlock
    ) -> SemanticContentWrapper:
        if name == '<institution>':
            return SemanticInstitution(layout_block=layout_block)
        if name == '<department>':
            return SemanticDepartment(layout_block=layout_block)
        if name == '<laboratory>':
            return SemanticLaboratory(layout_block=layout_block)
        if name == '<addrLine>':
            return SemanticAddressLine(layout_block=layout_block)
        if name == '<postCode>':
            return SemanticPostCode(layout_block=layout_block)
        if name == '<postBox>':
            return SemanticPostBox(layout_block=layout_block)
        if name == '<region>':
            return SemanticRegion(layout_block=layout_block)
        if name == '<settlement>':
            return SemanticSettlement(layout_block=layout_block)
        if name == '<country>':
            return SemanticCountry(layout_block=layout_block)
        return SemanticNote(
            layout_block=layout_block,
            note_type=name
        )

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
                aff = SemanticAffiliationAddress()
                aff.affiliation_id = next(ids_iterator, '?')
                aff.add_content(SemanticMarker(layout_block=layout_block))
                continue
            semantic_content = self.get_semantic_content_for_entity_name(
                name, layout_block
            )
            if not aff:
                if isinstance(semantic_content, SemanticNote):
                    yield semantic_content
                    continue
                aff = SemanticAffiliationAddress()
                aff.affiliation_id = next(ids_iterator,  '?')
            aff.add_content(semantic_content)
        if aff:
            yield aff
