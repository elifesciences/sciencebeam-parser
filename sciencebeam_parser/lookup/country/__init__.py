from abc import ABC, abstractmethod
from typing import Set


class CountryLookUp(ABC):
    @abstractmethod
    def is_country(self, text: str) -> bool:
        pass


class SimpleCountryLookUp(CountryLookUp):
    def __init__(self, valid_country_texts: Set[str]):
        self.valid_country_texts = {s.lower() for s in valid_country_texts}

    def is_country(self, text: str) -> bool:
        return text.lower() in self.valid_country_texts
