import math
from abc import ABC, abstractmethod
from typing import Iterable, List

from lxml import etree


ALTO_NS = 'http://www.loc.gov/standards/alto/ns-v3#'
ALTO_NS_MAP = {
    'alto': ALTO_NS
}


def alto_xpath(parent: etree.ElementBase, xpath: str) -> List[etree.ElementBase]:
    return parent.xpath(xpath, namespaces=ALTO_NS_MAP)


class ModelDataGenerator(ABC):
    @abstractmethod
    def iter_data_lines_for_xml_root(
        self,
        root: etree.ElementBase
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
