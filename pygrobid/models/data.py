import math
from abc import ABC, abstractmethod
from typing import Iterable

from lxml import etree

from pygrobid.document.layout_document import LayoutDocument
from pygrobid.external.pdfalto.parser import parse_alto_root


class ModelDataGenerator(ABC):
    def iter_data_lines_for_xml_root(
        self,
        root: etree.ElementBase
    ) -> Iterable[str]:
        return self.iter_data_lines_for_layout_document(
            parse_alto_root(root)
        )

    @abstractmethod
    def iter_data_lines_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> Iterable[str]:
        pass


def feature_linear_scaling_int(pos: int, total: int, bin_count: int) -> int:
    """
    Given an integer value between 0 and total, discretized into nbBins following a linear scale
    Adapted from:
    grobid-core/src/main/java/org/grobid/core/features/FeatureFactory.java
    """
    if pos >= total:
        return bin_count
    if pos <= 0:
        return 0
    return math.floor((pos / total) * bin_count)
