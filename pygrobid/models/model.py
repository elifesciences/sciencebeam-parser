from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

from pygrobid.models.data import ModelDataGenerator


class Model(ABC):
    @abstractmethod
    def get_data_generator(self) -> ModelDataGenerator:
        pass

    @abstractmethod
    def predict_labels(
        self,
        texts: List[List[str]],
        features: List[List[List[str]]],
        output_format: Optional[str] = None
    ) -> Iterable[str]:
        pass
