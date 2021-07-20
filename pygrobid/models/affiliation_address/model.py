import logging

from pygrobid.models.model import Model
from pygrobid.models.data import DEFAULT_DOCUMENT_FEATURES_CONTEXT, DocumentFeaturesContext
from pygrobid.models.affiliation_address.data import AffiliationAddressDataGenerator
from pygrobid.models.affiliation_address.extract import AffiliationAddressSemanticExtractor


LOGGER = logging.getLogger(__name__)


class AffiliationAddressModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext = DEFAULT_DOCUMENT_FEATURES_CONTEXT
    ) -> AffiliationAddressDataGenerator:
        return AffiliationAddressDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> AffiliationAddressSemanticExtractor:
        return AffiliationAddressSemanticExtractor()
