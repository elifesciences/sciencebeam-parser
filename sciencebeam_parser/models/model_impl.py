from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

from sciencebeam_parser.utils.lazy import Preloadable


class ModelImpl(ABC, Preloadable):
    @abstractmethod
    def predict_labels(
        self,
        texts: List[List[str]],
        features: List[List[List[str]]],
        output_format: Optional[str] = None
    ) -> List[List[Tuple[str, str]]]:
        pass


T_ModelImplFactory = Callable[[], ModelImpl]
