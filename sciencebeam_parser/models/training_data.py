import logging
from typing import Iterable, List, Mapping, Optional, Sequence

from lxml import etree
from lxml.builder import ElementMaker

from sciencebeam_parser.utils.xml_writer import XmlTreeWriter
from sciencebeam_parser.document.tei.common import TEI_E
from sciencebeam_parser.document.layout_document import (
    LayoutLine
)
from sciencebeam_parser.models.model import get_split_prefix_label
from sciencebeam_parser.models.data import LabeledLayoutModelData, LayoutModelData


LOGGER = logging.getLogger(__name__)


NO_NS_TEI_E = ElementMaker()


OTHER_LABELS = {'<other>', 'O'}


def get_model_data_label(model_data: LayoutModelData) -> Optional[str]:
    if isinstance(model_data, LabeledLayoutModelData):
        return model_data.label
    return None


def is_same_layout_line(
    layout_line_1: Optional[LayoutLine],
    layout_line_2: Optional[LayoutLine]
) -> bool:
    assert layout_line_1 is not None
    assert layout_line_2 is not None
    return id(layout_line_1) == id(layout_line_2)


def is_same_model_data_layout_line(
    model_data_1: LayoutModelData,
    model_data_2: LayoutModelData
) -> bool:
    return is_same_layout_line(model_data_1.layout_line, model_data_2.layout_line)


def iter_group_model_data_by_line(
    model_data_iterable: Iterable[LayoutModelData]
) -> Iterable[Sequence[LayoutModelData]]:
    line_model_data_list: List[LayoutModelData] = []
    for model_data in model_data_iterable:
        if not line_model_data_list:
            line_model_data_list.append(model_data)
            continue
        previous_model_data = line_model_data_list[-1]
        if is_same_model_data_layout_line(
            model_data,
            previous_model_data
        ):
            LOGGER.debug('same line: %r - %r', model_data, previous_model_data)
            line_model_data_list.append(model_data)
            continue
        yield line_model_data_list
        line_model_data_list = [model_data]
    if line_model_data_list:
        yield line_model_data_list


def get_default_note_type_for_label(label: str) -> str:
    return label.strip('<>')


def is_parent_path_of(
    parent_path: Sequence[str],
    child_path: Sequence[str]
) -> bool:
    if len(parent_path) >= len(child_path):
        return False
    return tuple(child_path[:len(parent_path)]) == tuple(parent_path)


def is_same_or_parent_path_of(
    parent_path: Sequence[str],
    child_path: Sequence[str]
) -> bool:
    return (
        tuple(parent_path) == tuple(child_path)
        or is_parent_path_of(parent_path, child_path)
    )


class AbstractTeiTrainingDataGenerator:
    def __init__(
        self,
        root_training_xml_element_path: Sequence[str],
        training_xml_element_path_by_label: Mapping[str, Sequence[str]],
        root_tag: str = 'tei',
        use_tei_namespace: bool = True,
        element_maker: Optional[ElementMaker] = None,
        reset_training_xml_element_path_by_label: Optional[Mapping[str, Sequence[str]]] = None,
        default_tei_filename_suffix: Optional[str] = None,
        default_data_filename_suffix: Optional[str] = None
    ):
        self.root_training_xml_element_path = root_training_xml_element_path
        self.root_parent_training_xml_element_path = root_training_xml_element_path[:-1]
        self.training_xml_element_path_by_label = training_xml_element_path_by_label
        self.reset_training_xml_element_path_by_label = (
            reset_training_xml_element_path_by_label or {}
        )
        self._training_xml_element_paths = {
            tuple(element_path)
            for label, element_path in training_xml_element_path_by_label.items()
            if (
                label not in OTHER_LABELS
                and tuple(element_path) != tuple(root_training_xml_element_path)
            )
        }
        self.other_element_path = training_xml_element_path_by_label.get('<other>')
        if element_maker is None:
            element_maker = TEI_E if use_tei_namespace else NO_NS_TEI_E
        self.element_maker = element_maker
        self.root_tag = root_tag
        self.default_tei_filename_suffix = default_tei_filename_suffix
        self.default_data_filename_suffix = default_data_filename_suffix

    def get_default_tei_filename_suffix(self) -> Optional[str]:
        return self.default_tei_filename_suffix

    def get_default_data_filename_suffix(self) -> Optional[str]:
        return self.default_data_filename_suffix

    def get_training_xml_path_for_label(
        self,
        label: Optional[str],
        current_path: Sequence[str]
    ) -> Sequence[str]:
        if not label or label in OTHER_LABELS:
            if label and self.other_element_path is not None:
                return self.other_element_path
            if tuple(current_path) in self._training_xml_element_paths:
                LOGGER.debug(
                    'found current path in element paths, returning parent: %r', current_path
                )
                return current_path[:-1]
            LOGGER.debug(
                'not found current path in element paths, returning current: %r', current_path
            )
            return current_path
        training_xml_path = self.training_xml_element_path_by_label.get(label or '')
        if not training_xml_path:
            note_type = get_default_note_type_for_label(label)
            LOGGER.info('label not mapped, creating note: %r', label)
            training_xml_path = (
                list(self.root_training_xml_element_path) + [f'note[@type="{note_type}"]']
            )
        return training_xml_path

    def get_reset_training_xml_path_for_label(
        self,
        label: Optional[str],
        prefix: Optional[str]
    ) -> Optional[Sequence[str]]:
        if prefix != 'B' or not label:
            return None
        return self.reset_training_xml_element_path_by_label.get(label)

    def write_xml_for_model_data_iterable(
        self,
        xml_writer: XmlTreeWriter,
        model_data_iterable: Iterable[LayoutModelData]
    ):
        default_path = xml_writer.current_path
        LOGGER.debug('default_path: %r', default_path)
        pending_whitespace = ''
        prev_label: str = ''
        for line_model_data_list in iter_group_model_data_by_line(model_data_iterable):
            for model_data in line_model_data_list:
                layout_token = model_data.layout_token
                assert layout_token is not None
                prefixed_label = get_model_data_label(model_data)
                prefix, label = get_split_prefix_label(prefixed_label or '')
                xml_element_path = self.get_training_xml_path_for_label(
                    label,
                    current_path=xml_writer.current_path
                )
                reset_path = self.get_reset_training_xml_path_for_label(
                    label=label,
                    prefix=prefix
                )
                LOGGER.debug(
                    'label: %r (%r: %r; reset_path=%r)',
                    label, prefix, xml_element_path, reset_path
                )
                if reset_path is not None:
                    xml_writer.require_path(reset_path)
                elif (
                    prev_label not in OTHER_LABELS
                    and pending_whitespace
                    and not is_same_or_parent_path_of(xml_writer.current_path, xml_element_path)
                ):
                    LOGGER.debug(
                        'closing element before adding whitespace, %r -> %r',
                        xml_writer.current_path, xml_element_path
                    )
                    xml_writer.require_path(xml_writer.current_path[:-1])
                elif prefix == 'B' and label not in OTHER_LABELS:
                    xml_writer.require_path(xml_element_path[:-1])
                xml_writer.require_path_or_below(xml_element_path)
                xml_writer.append_text(pending_whitespace)
                pending_whitespace = ''
                xml_writer.require_path(xml_element_path)
                xml_writer.append_text(layout_token.text)
                pending_whitespace = layout_token.whitespace
                prev_label = label
            xml_writer.append(self.element_maker('lb'))
            pending_whitespace = '\n'
        xml_writer.require_path(default_path)
        xml_writer.append_text(pending_whitespace)

    def _get_xml_writer(self) -> XmlTreeWriter:
        return XmlTreeWriter(
            self.element_maker(self.root_tag),
            element_maker=self.element_maker
        )

    def get_post_processed_xml_root(self, xml_root: etree.ElementBase):
        return xml_root

    def get_training_tei_xml_for_multiple_model_data_iterables(
        self,
        model_data_iterables: Iterable[Iterable[LayoutModelData]]
    ) -> etree.ElementBase:
        xml_writer = self._get_xml_writer()
        xml_writer.require_path(self.root_parent_training_xml_element_path)
        for model_data_iterable in model_data_iterables:
            xml_writer.require_path(self.root_parent_training_xml_element_path)
            xml_writer.require_path(self.root_training_xml_element_path)
            self.write_xml_for_model_data_iterable(
                xml_writer,
                model_data_iterable=model_data_iterable
            )
        return self.get_post_processed_xml_root(xml_writer.root)

    def get_training_tei_xml_for_model_data_iterable(
        self,
        model_data_iterable: Iterable[LayoutModelData]
    ) -> etree.ElementBase:
        return self.get_training_tei_xml_for_multiple_model_data_iterables(
            [model_data_iterable]
        )
