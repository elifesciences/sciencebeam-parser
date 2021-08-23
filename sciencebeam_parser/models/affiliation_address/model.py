import logging

from sciencebeam_parser.models.model import Model
from sciencebeam_parser.models.data import (
    DocumentFeaturesContext
)
from sciencebeam_parser.models.affiliation_address.data import AffiliationAddressDataGenerator
from sciencebeam_parser.models.affiliation_address.extract import (
    AffiliationAddressSemanticExtractor
)


LOGGER = logging.getLogger(__name__)


class AffiliationAddressModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext
    ) -> AffiliationAddressDataGenerator:
        return AffiliationAddressDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> AffiliationAddressSemanticExtractor:
        return AffiliationAddressSemanticExtractor()
