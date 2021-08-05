from abc import ABC, abstractmethod
from typing import List, Optional, Sequence, Set


class TextLookUp(ABC):
    @abstractmethod
    def contains(self, text: str) -> bool:
        pass


class SimpleTextLookUp(TextLookUp):
    def __init__(self, valid_texts: Set[str]):
        self.valid_texts = {s.lower() for s in valid_texts}

    def contains(self, text: str) -> bool:
        return text.lower() in self.valid_texts


class MergedTextLookUp(TextLookUp):
    def __init__(self, lookups: Sequence[Optional[TextLookUp]]):
        self.lookups: List[TextLookUp] = [
            lookup
            for lookup in lookups
            if lookup is not None
        ]

    def contains(self, text: str) -> bool:
        for lookup in self.lookups:
            if lookup.contains(text):
                return True
        return False
