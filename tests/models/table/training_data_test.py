import logging
from typing import Iterable, Sequence

import pytest

from lxml import etree
from lxml.builder import E

from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutLine
)
from sciencebeam_parser.document.tei.common import (
    get_tei_xpath_text_content_list,
    tei_xpath
)
from sciencebeam_parser.models.data import (
    DEFAULT_DOCUMENT_FEATURES_CONTEXT,
    LayoutModelData
)
from sciencebeam_parser.models.fulltext.data import FullTextDataGenerator
from sciencebeam_parser.models.table.training_data import (
    ROOT_TRAINING_XML_ELEMENT_PATH,
    TRAINING_XML_ELEMENT_PATH_BY_LABEL,
    TableTeiTrainingDataGenerator,
    TableTrainingTeiParser
)
from sciencebeam_parser.utils.xml import get_text_content
from sciencebeam_parser.utils.xml_writer import XmlTreeWriter

from tests.test_utils import log_on_exception
from tests.models.training_data_test_utils import (
    get_labeled_model_data_list,
    get_labeled_model_data_list_list,
    get_model_data_list_for_layout_document,
    get_next_layout_line_for_text
)


LOGGER = logging.getLogger(__name__)


TEXT_1 = 'this is text 1'
TEXT_2 = 'this is text 2'


TOKEN_1 = 'token1'
TOKEN_2 = 'token2'
TOKEN_3 = 'token3'
TOKEN_4 = 'token4'


TABLE_XPATH = './text/figure[@type="table"]'


def get_data_generator() -> FullTextDataGenerator:
    return FullTextDataGenerator(DEFAULT_DOCUMENT_FEATURES_CONTEXT)


def get_tei_training_data_generator() -> TableTeiTrainingDataGenerator:
    return TableTeiTrainingDataGenerator()


def get_training_tei_parser() -> TableTrainingTeiParser:
    return TableTrainingTeiParser()


def get_training_tei_xml_for_model_data_iterable(
    model_data_iterable: Iterable[LayoutModelData]
) -> etree.ElementBase:
    training_data_generator = get_tei_training_data_generator()
    xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
        model_data_iterable
    )
    LOGGER.debug('xml: %r', etree.tostring(xml_root))
    return xml_root


def get_training_tei_xml_for_layout_document(
    layout_document: LayoutDocument
) -> etree.ElementBase:
    return get_training_tei_xml_for_model_data_iterable(
        get_model_data_list_for_layout_document(
            layout_document,
            data_generator=get_data_generator()
        )
    )


@log_on_exception
class TestFigureTeiTrainingDataGenerator:
    def test_should_include_layout_document_text_in_tei_output(self):
        layout_document = LayoutDocument.for_blocks([LayoutBlock.for_text(TEXT_1)])
        xml_root = get_training_tei_xml_for_layout_document(layout_document)
        nodes = tei_xpath(xml_root, TABLE_XPATH)
        assert len(nodes) == 1
        assert get_text_content(nodes[0]).rstrip() == TEXT_1

    def test_should_keep_original_whitespace(self):
        text = 'Token1, Token2  ,Token3'
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(text, tail_whitespace='\n')
        ])])
        xml_root = get_training_tei_xml_for_layout_document(layout_document)
        nodes = tei_xpath(xml_root, TABLE_XPATH)
        assert len(nodes) == 1
        assert get_text_content(nodes[0]).rstrip() == text

    def test_should_add_line_feeds(self):
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = get_training_tei_xml_for_layout_document(layout_document)
        nodes = tei_xpath(xml_root, TABLE_XPATH)
        assert len(nodes) == 1
        assert get_text_content(nodes[0]).rstrip() == '\n'.join([TEXT_1, TEXT_2])

    def test_should_lb_elements_before_line_feeds(self):
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = get_training_tei_xml_for_layout_document(layout_document)
        nodes = tei_xpath(xml_root, TABLE_XPATH)
        assert len(nodes) == 1
        lb_nodes = tei_xpath(nodes[0], 'lb')
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
        xml_root = get_training_tei_xml_for_model_data_iterable(model_data_iterable)
        nodes = tei_xpath(xml_root, TABLE_XPATH)
        assert len(nodes) == 1
        lb_nodes = tei_xpath(nodes[0], 'lb')
        assert len(lb_nodes) == 2
        assert lb_nodes[0].getparent().text == TEXT_1
        assert lb_nodes[0].tail == '\n' + TEXT_2

    def test_should_generate_tei_for_most_labels(self):
        label_and_layout_line_list = [
            ('<figure_head>', get_next_layout_line_for_text('Table Head 1')),
            ('<figDesc>', get_next_layout_line_for_text('Table Desc 1')),
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        xml_root = get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/head'
        ) == ['Table Head 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/figDesc'
        ) == ['Table Desc 1']

    def test_should_add_label_at_the_end_inside_head_element(self):
        label_and_layout_line_list = [
            ('<figure_head>', get_next_layout_line_for_text('Table Head 1')),
            ('<label>', get_next_layout_line_for_text('Table Label 1'))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        xml_root = get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/head/label'
        ) == ['Table Label 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/head'
        ) == ['\n'.join(['Table Head 1', 'Table Label 1'])]

    def test_should_add_label_in_the_middle_inside_head_element(self):
        label_and_layout_line_list = [
            ('<figure_head>', get_next_layout_line_for_text('Table Head 1')),
            ('<label>', get_next_layout_line_for_text('Table Label 1')),
            ('I-<figure_head>', get_next_layout_line_for_text('Continued Table Head 1'))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        xml_root = get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/head/label'
        ) == ['Table Label 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/head'
        ) == ['\n'.join(['Table Head 1', 'Table Label 1', 'Continued Table Head 1'])]

    def test_should_add_label_to_head_element_without_additional_text(self):
        label_and_layout_line_list = [
            ('<label>', get_next_layout_line_for_text('Table Label 1')),
            ('<figDesc>', get_next_layout_line_for_text('Table Desc 1')),
            ('<content>', get_next_layout_line_for_text('Content 1')),
            ('<other>', get_next_layout_line_for_text('Other 1')),
            ('<note>', get_next_layout_line_for_text('Note 1'))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        xml_root = get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/head/label'
        ) == ['Table Label 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/head'
        ) == ['Table Label 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/figDesc'
        ) == ['Table Desc 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/table'
        ) == ['Content 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/other'
        ) == ['Other 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/note'
        ) == ['Note 1']

    def test_should_map_unknown_label_to_note(self):
        label_and_layout_line_list = [
            ('<unknown>', get_next_layout_line_for_text(TEXT_1))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        xml_root = get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        assert get_tei_xpath_text_content_list(
            xml_root, f'{TABLE_XPATH}/note[@type="unknown"]'
        ) == [TEXT_1]

    def test_should_generate_tei_from_multiple_model_data_lists_using_model_labels(self):
        label_and_layout_line_list_list = [
            [
                ('<figure_head>', get_next_layout_line_for_text(TEXT_1))
            ], [
                ('<figure_head>', get_next_layout_line_for_text(TEXT_2))
            ]
        ]
        labeled_model_data_list_list = get_labeled_model_data_list_list(
            label_and_layout_line_list_list,
            data_generator=get_data_generator()
        )
        training_data_generator = get_tei_training_data_generator()
        xml_root = training_data_generator.get_training_tei_xml_for_multiple_model_data_iterables(
            labeled_model_data_list_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        nodes = tei_xpath(xml_root, TABLE_XPATH)
        assert len(nodes) == 2
        assert get_tei_xpath_text_content_list(
            nodes[0], './head'
        ) == [TEXT_1]
        assert get_tei_xpath_text_content_list(
            nodes[1], './head'
        ) == [TEXT_2]


# pylint: disable=not-callable

def _get_training_tei_with_tables(
    figures: Sequence[etree.ElementBase]
) -> etree.ElementBase:
    xml_writer = XmlTreeWriter(E('tei'), element_maker=E)
    xml_writer.require_path(
        ROOT_TRAINING_XML_ELEMENT_PATH[:-1]
    )
    xml_writer.append_all(*figures)
    LOGGER.debug('training tei: %r', etree.tostring(xml_writer.root))
    return xml_writer.root


class TestTableTrainingTeiParser:
    def test_should_parse_single_token_labelled_training_tei_lines(self):
        tei_root = _get_training_tei_with_tables([E(
            'figure',
            {'type': 'table'},
            E('head', TOKEN_1, E('lb')),
            '\n',
            E('figDesc', TOKEN_2, E('lb')),
            '\n'
        )])
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        assert tag_result == [[
            (TOKEN_1, 'B-<figure_head>'),
            (TOKEN_2, 'B-<figDesc>')
        ]]

    def test_should_parse_single_label_with_multiple_lines(self):
        tei_root = _get_training_tei_with_tables([E(
            'figure',
            {'type': 'table'},
            E('figDesc', TOKEN_1, E('lb'), '\n', TOKEN_2, E('lb')),
            '\n'
        )])
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        assert tag_result == [[
            (TOKEN_1, 'B-<figDesc>'),
            (TOKEN_2, 'I-<figDesc>')
        ]]

    def test_should_parse_figure_head_with_label(self):
        tei_root = _get_training_tei_with_tables([E(
            'figure',
            {'type': 'table'},
            E(
                'head',
                TOKEN_1,
                ' ',
                E('label', TOKEN_2, E('lb'))
            ),
            '\n'
        )])
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        assert tag_result == [[
            (TOKEN_1, 'B-<figure_head>'),
            (TOKEN_2, 'B-<label>')
        ]]

    def test_should_parse_figure_head_with_label_and_continued_head(self):
        tei_root = _get_training_tei_with_tables([E(
            'figure',
            {'type': 'table'},
            E(
                'head',
                TOKEN_1,
                ' ',
                E('label', TOKEN_2, E('lb')),
                ' ',
                TOKEN_3
            ),
            '\n'
        )])
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        assert tag_result == [[
            (TOKEN_1, 'B-<figure_head>'),
            (TOKEN_2, 'B-<label>'),
            (TOKEN_3, 'I-<figure_head>')
        ]]

    def test_should_interpret_text_in_figure_as_unlabelled(self):
        tei_root = _get_training_tei_with_tables([E(
            'figure', {'type': 'table'}, TOKEN_1, E('lb'), '\n'
        )])
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        assert tag_result == [[
            (TOKEN_1, 'O')
        ]]

    def test_should_output_multiple_tokens_of_each_unlabelled_lines(self):
        tei_root = _get_training_tei_with_tables([E(
            'figure',
            {'type': 'table'},
            TOKEN_1,
            ' ',
            TOKEN_2,
            E('lb'),
            '\n',
            TOKEN_3,
            ' ',
            TOKEN_4,
            E('lb'),
            '\n'
        )])
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        LOGGER.debug('tag_result: %r', tag_result)
        assert tag_result == [[
            (TOKEN_1, 'O'),
            (TOKEN_2, 'O'),
            (TOKEN_3, 'O'),
            (TOKEN_4, 'O')
        ]]

    def test_should_parse_single_label_with_multiple_tokens_on_multiple_lines(self):
        tei_root = _get_training_tei_with_tables([E(
            'figure',
            {'type': 'table'},
            E(
                'figDesc',
                TOKEN_1,
                ' ',
                TOKEN_2,
                E('lb'),
                '\n',
                TOKEN_3,
                ' ',
                TOKEN_4,
                E('lb')
            ),
            '\n'
        )])
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        LOGGER.debug('tag_result: %r', tag_result)
        assert tag_result == [[
            (TOKEN_1, 'B-<figDesc>'),
            (TOKEN_2, 'I-<figDesc>'),
            (TOKEN_3, 'I-<figDesc>'),
            (TOKEN_4, 'I-<figDesc>')
        ]]

    @pytest.mark.parametrize(
        "tei_label,element_path",
        list(TRAINING_XML_ELEMENT_PATH_BY_LABEL.items())
    )
    def test_should_parse_all_supported_labels(
        self,
        tei_label: str,
        element_path: Sequence[str]
    ):
        xml_writer = XmlTreeWriter(E('tei'), element_maker=E)
        xml_writer.require_path(element_path)
        xml_writer.append_all(
            TOKEN_1,
            ' ',
            TOKEN_2,
            E('lb'),
            '\n',
            TOKEN_3,
            ' ',
            TOKEN_4,
            E('lb')
        )
        tei_root = xml_writer.root
        LOGGER.debug('tei_root: %r', etree.tostring(tei_root))
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        LOGGER.debug('tag_result: %r', tag_result)
        if tei_label == '<other>':
            assert tag_result == [[
                (TOKEN_1, tei_label),
                (TOKEN_2, tei_label),
                (TOKEN_3, tei_label),
                (TOKEN_4, tei_label)
            ]]
        else:
            assert tag_result == [[
                (TOKEN_1, f'B-{tei_label}'),
                (TOKEN_2, f'I-{tei_label}'),
                (TOKEN_3, f'I-{tei_label}'),
                (TOKEN_4, f'I-{tei_label}')
            ]]
