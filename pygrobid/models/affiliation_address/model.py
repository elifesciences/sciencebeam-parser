import logging

from pygrobid.models.model import Model
from pygrobid.models.affiliation_address.data import AffiliationAddressDataGenerator
from pygrobid.models.affiliation_address.extract import AffiliationAddressSemanticExtractor


LOGGER = logging.getLogger(__name__)


class AffiliationAddressModel(Model):
    def get_data_generator(self) -> AffiliationAddressDataGenerator:
        return AffiliationAddressDataGenerator()

    def get_semantic_extractor(self) -> AffiliationAddressSemanticExtractor:
        return AffiliationAddressSemanticExtractor()