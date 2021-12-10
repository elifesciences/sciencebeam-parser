import logging
from typing import Sequence, Tuple

from lxml import etree

from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutLine,
    LayoutLineDescriptor
)
from sciencebeam_parser.document.tei.common import tei_xpath
from sciencebeam_parser.models.data import (
    DEFAULT_DOCUMENT_FEATURES_CONTEXT,
    LabeledLayoutModelData,
    LayoutModelData
)
from sciencebeam_parser.models.fulltext.data import FullTextDataGenerator
from sciencebeam_parser.models.fulltext.training_data import (
    FullTextTeiTrainingDataGenerator
)
from sciencebeam_parser.utils.xml import get_text_content, get_text_content_list


LOGGER = logging.getLogger(__name__)


TEXT_1 = 'this is text 1'
TEXT_2 = 'this is text 2'


def get_data_generator() -> FullTextDataGenerator:
    return FullTextDataGenerator(DEFAULT_DOCUMENT_FEATURES_CONTEXT)


def get_model_data_list_for_layout_document(
    layout_document: LayoutDocument
) -> Sequence[LayoutModelData]:
    data_generator = get_data_generator()
    return list(data_generator.iter_model_data_for_layout_document(
        layout_document
    ))


def get_labeled_model_data_list(
    label_and_layout_line_list: Sequence[Tuple[str, LayoutLine]]
) -> Sequence[LabeledLayoutModelData]:
    data_generator = get_data_generator()
    labeled_model_data_list = []
    for label, layout_line in label_and_layout_line_list:
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[layout_line])])
        labeled_model_data_list.extend([
            LabeledLayoutModelData.from_model_data(
                model_data,
                label=('B-' if index == 0 else 'I-') + label
            )
            for index, model_data in enumerate(
                data_generator.iter_model_data_for_layout_document(
                    layout_document
                )
            )
        ])
    return labeled_model_data_list


def get_labeled_model_data_list_list(
    label_and_layout_line_list_list: Sequence[Sequence[Tuple[str, LayoutLine]]]
) -> Sequence[Sequence[LabeledLayoutModelData]]:
    return [
        get_labeled_model_data_list(label_and_layout_line_list)
        for label_and_layout_line_list in label_and_layout_line_list_list
    ]


def get_layout_line_for_text(text: str, line_id: int) -> LayoutLine:
    return LayoutLine.for_text(
        text,
        tail_whitespace='\n',
        line_descriptor=LayoutLineDescriptor(line_id=line_id)
    )


class ModuleState:
    line_id: int = 1


def get_next_layout_line_for_text(text: str) -> LayoutLine:
    line_id = ModuleState.line_id
    ModuleState.line_id += 1
    return get_layout_line_for_text(text, line_id=line_id)


class TestFullTextTeiTrainingDataGenerator:
    def test_should_include_layout_document_text_in_tei_output(self):
        training_data_generator = FullTextTeiTrainingDataGenerator()
        layout_document = LayoutDocument.for_blocks([LayoutBlock.for_text(TEXT_1)])
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            get_model_data_list_for_layout_document(layout_document)
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        text_nodes = tei_xpath(xml_root, './text')
        assert len(text_nodes) == 1
        assert get_text_content(text_nodes[0]).rstrip() == TEXT_1

    def test_should_keep_original_whitespace(self):
        training_data_generator = FullTextTeiTrainingDataGenerator()
        text = 'Token1, Token2  ,Token3'
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(text, tail_whitespace='\n')
        ])])
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            get_model_data_list_for_layout_document(layout_document)
        )
        text_nodes = xml_root.xpath('./text')
        assert len(text_nodes) == 1
        assert get_text_content(text_nodes[0]).rstrip() == text

    def test_should_add_line_feeds(self):
        training_data_generator = FullTextTeiTrainingDataGenerator()
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            get_model_data_list_for_layout_document(layout_document)
        )
        text_nodes = xml_root.xpath('./text')
        assert len(text_nodes) == 1
        assert get_text_content(text_nodes[0]).rstrip() == '\n'.join([TEXT_1, TEXT_2])

    def test_should_lb_elements_before_line_feeds(self):
        training_data_generator = FullTextTeiTrainingDataGenerator()
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            get_model_data_list_for_layout_document(layout_document)
        )
        text_nodes = xml_root.xpath('./text')
        assert len(text_nodes) == 1
        lb_nodes = text_nodes[0].xpath('lb')
        assert len(lb_nodes) == 2
        assert lb_nodes[0].getparent().text == TEXT_1
        assert lb_nodes[0].tail == '\n' + TEXT_2

    def test_should_generate_tei_from_model_data(self):
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            get_next_layout_line_for_text(TEXT_1),
            get_next_layout_line_for_text(TEXT_2)
        ])])
        data_generator = get_data_generator()
        model_data_iterable = data_generator.iter_model_data_for_layout_document(
            layout_document
        )
        training_data_generator = FullTextTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            model_data_iterable
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        text_nodes = xml_root.xpath('./text')
        assert len(text_nodes) == 1
        lb_nodes = text_nodes[0].xpath('lb')
        assert len(lb_nodes) == 2
        assert lb_nodes[0].getparent().text == TEXT_1
        assert lb_nodes[0].tail == '\n' + TEXT_2

    def test_should_generate_tei_from_model_data_using_model_labels(self):
        label_and_layout_line_list = [
            ('<section>', get_next_layout_line_for_text(TEXT_1)),
            ('<paragraph>', get_next_layout_line_for_text(TEXT_2))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list
        )
        training_data_generator = FullTextTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert get_text_content_list(
            xml_root.xpath('./text/head')
        ) == [TEXT_1]
        assert get_text_content_list(
            xml_root.xpath('./text/p')
        ) == [TEXT_2]
        assert get_text_content_list(
            xml_root.xpath('./text')
        ) == [f'{TEXT_1}\n{TEXT_2}\n']

    def test_should_map_unknown_label_to_note(self):
        label_and_layout_line_list = [
            ('<unknown>', get_next_layout_line_for_text(TEXT_1))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list
        )
        training_data_generator = FullTextTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert get_text_content_list(
            xml_root.xpath('./text/note[@type="unknown"]')
        ) == [TEXT_1]
        assert get_text_content_list(
            xml_root.xpath('./text')
        ) == [f'{TEXT_1}\n']

    def test_should_not_join_separate_labels(self):
        label_and_layout_line_list = [
            ('<section>', get_next_layout_line_for_text(TEXT_1)),
            ('<section>', get_next_layout_line_for_text(TEXT_2))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list
        )
        training_data_generator = FullTextTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert get_text_content_list(
            xml_root.xpath('./text/head')
        ) == [TEXT_1, TEXT_2]
        assert get_text_content_list(
            xml_root.xpath('./text')
        ) == [f'{TEXT_1}\n{TEXT_2}\n']
