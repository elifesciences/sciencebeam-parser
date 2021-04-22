import logging
from typing import Iterable, Tuple

from pygrobid.document.tei_document import TeiDocument
from pygrobid.models.header.data import HeaderDataGenerator
from pygrobid.models.delft_model import DelftModel


LOGGER = logging.getLogger(__name__)


class HeaderModel(DelftModel):
    def get_data_generator(self) -> HeaderDataGenerator:
        return HeaderDataGenerator()

    def update_document_with_entity_values(
        self,
        document: TeiDocument,
        entity_values: Iterable[Tuple[str, str]]
    ):
        entity_values = list(entity_values)
        LOGGER.info('entity_values: %s', entity_values)
        current_title = None
        current_abstract = None
        for name, value in entity_values:
            if name == '<title>' and not current_title:
                current_title = value
                document.set_title(value)
            if name == '<abstract>' and not current_abstract:
                current_abstract = value
                document.set_abstract(value)
