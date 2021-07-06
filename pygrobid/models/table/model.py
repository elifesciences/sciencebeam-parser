import logging

from pygrobid.models.model import Model
from pygrobid.models.fulltext.data import FullTextDataGenerator
from pygrobid.models.table.extract import TableSemanticExtractor


LOGGER = logging.getLogger(__name__)


class TableModel(Model):
    def get_data_generator(self) -> FullTextDataGenerator:
        return FullTextDataGenerator()

    def get_semantic_extractor(self) -> TableSemanticExtractor:
        return TableSemanticExtractor()
