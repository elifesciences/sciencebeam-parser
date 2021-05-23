import logging
import re
from typing import Iterable, Tuple

from pygrobid.document.tei_document import TeiDocument
from pygrobid.models.header.data import HeaderDataGenerator
from pygrobid.models.delft_model import DelftModel


LOGGER = logging.getLogger(__name__)


# based on:
#   grobid-core/src/main/java/org/grobid/core/data/BiblioItem.java
ABSTRACT_REGEX = r'^(?:(?:abstract|summary|résumé|abrégé|a b s t r a c t)(?:[.:])?)?\s*(.*)'


def get_cleaned_abstract_text(text: str) -> str:
    if not text:
        return text
    m = re.match(ABSTRACT_REGEX, text, re.IGNORECASE)
    if not m:
        LOGGER.debug('text does not match regex: %r', text)
        return text
    return m.group(1)


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
                value = get_cleaned_abstract_text(value)
                current_abstract = value
                document.set_abstract(value)
