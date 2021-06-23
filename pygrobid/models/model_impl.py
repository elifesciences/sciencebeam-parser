from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple


class ModelImpl(ABC):
    @abstractmethod
    def predict_labels(
        self,
        texts: List[List[str]],
        features: List[List[List[str]]],
        output_format: Optional[str] = None
    ) -> List[List[Tuple[str, str]]]:
        pass


T_ModelImplFactory = Callable[[], ModelImpl]
