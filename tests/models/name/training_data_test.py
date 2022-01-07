import logging
from typing import Iterable

from lxml import etree

from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutLine
)
from sciencebeam_parser.document.tei.common import (
    TEI_NS_PREFIX,
    get_tei_xpath_text_content_list,
    tei_xpath
)
from sciencebeam_parser.models.data import (
    DEFAULT_DOCUMENT_FEATURES_CONTEXT,
    LayoutModelData
)
from sciencebeam_parser.models.name.data import NameDataGenerator
from sciencebeam_parser.models.name.training_data import (
    NameTeiTrainingDataGenerator
)
from sciencebeam_parser.utils.xml import get_text_content

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


AUTHOR_XPATH = (
    './tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:biblStruct/tei:analytic/tei:author'
    '/tei:persName'
)


def get_data_generator() -> NameDataGenerator:
    return NameDataGenerator(DEFAULT_DOCUMENT_FEATURES_CONTEXT)


def get_tei_training_data_generator() -> NameTeiTrainingDataGenerator:
    return NameTeiTrainingDataGenerator()


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
        assert xml_root.tag == f'{TEI_NS_PREFIX}TEI'
        nodes = tei_xpath(xml_root, AUTHOR_XPATH)
        assert len(nodes) == 1
        assert get_text_content(nodes[0]).rstrip() == TEXT_1

    def test_should_keep_original_whitespace(self):
        text = 'Token1, Token2  ,Token3'
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(text, tail_whitespace='\n')
        ])])
        xml_root = get_training_tei_xml_for_layout_document(layout_document)
        nodes = tei_xpath(xml_root, AUTHOR_XPATH)
        assert len(nodes) == 1
        assert get_text_content(nodes[0]).rstrip() == text

    def test_should_add_line_feeds(self):
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = get_training_tei_xml_for_layout_document(layout_document)
        nodes = tei_xpath(xml_root, AUTHOR_XPATH)
        assert len(nodes) == 1
        assert get_text_content(nodes[0]).rstrip() == '\n'.join([TEXT_1, TEXT_2])

    def test_should_lb_elements_before_line_feeds(self):
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = get_training_tei_xml_for_layout_document(layout_document)
        nodes = tei_xpath(xml_root, AUTHOR_XPATH)
        assert len(nodes) == 1
        lb_nodes = tei_xpath(nodes[0], 'tei:lb')
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
        nodes = tei_xpath(xml_root, AUTHOR_XPATH)
        assert len(nodes) == 1
        lb_nodes = tei_xpath(nodes[0], 'tei:lb')
        assert len(lb_nodes) == 2
        assert lb_nodes[0].getparent().text == TEXT_1
        assert lb_nodes[0].tail == '\n' + TEXT_2

    def test_should_generate_tei_for_most_labels(self):
        label_and_layout_line_list = [
            ('<marker>', get_next_layout_line_for_text('Marker 1')),
            ('<title>', get_next_layout_line_for_text('Title 1')),
            ('<forename>', get_next_layout_line_for_text('Forename 1')),
            ('<middlename>', get_next_layout_line_for_text('Middlename 1')),
            ('<surname>', get_next_layout_line_for_text('Surname 1')),
            ('<suffix>', get_next_layout_line_for_text('Suffix 1')),
            ('<other>', get_next_layout_line_for_text('Other 1')),
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        xml_root = get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        assert get_tei_xpath_text_content_list(
            xml_root, f'{AUTHOR_XPATH}/tei:marker'
        ) == ['Marker 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{AUTHOR_XPATH}/tei:roleName'
        ) == ['Title 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{AUTHOR_XPATH}/tei:forename'
        ) == ['Forename 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{AUTHOR_XPATH}/tei:middlename'
        ) == ['Middlename 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{AUTHOR_XPATH}/tei:surname'
        ) == ['Surname 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{AUTHOR_XPATH}/tei:suffix'
        ) == ['Suffix 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{AUTHOR_XPATH}/tei:other'
        ) == ['Other 1']

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
            xml_root, f'{AUTHOR_XPATH}/tei:note[@type="unknown"]'
        ) == [TEXT_1]

    def test_should_generate_tei_from_multiple_model_data_lists_using_model_labels(self):
        label_and_layout_line_list_list = [
            [
                ('<forename>', get_next_layout_line_for_text(TEXT_1))
            ], [
                ('<forename>', get_next_layout_line_for_text(TEXT_2))
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
        nodes = tei_xpath(xml_root, AUTHOR_XPATH)
        assert len(nodes) == 2
        assert get_tei_xpath_text_content_list(
            nodes[0], './tei:forename'
        ) == [TEXT_1]
        assert get_tei_xpath_text_content_list(
            nodes[1], './tei:forename'
        ) == [TEXT_2]

    def test_should_split_on_comma_before_marker(self):
        label_and_layout_line_list_list = [
            [
                ('<marker>', get_next_layout_line_for_text('1')),
                ('<forename>', get_next_layout_line_for_text('John')),
                ('<surname>', get_next_layout_line_for_text('Smith')),
                ('O', get_next_layout_line_for_text(',')),
                ('<forename>', get_next_layout_line_for_text('Maria')),
                ('<surname>', get_next_layout_line_for_text('Madison'))
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
        nodes = tei_xpath(xml_root, AUTHOR_XPATH)
        assert len(nodes) == 2
        assert get_tei_xpath_text_content_list(
            nodes[0], './tei:forename'
        ) == ['John']
        assert get_tei_xpath_text_content_list(
            nodes[1], './tei:forename'
        ) == ['Maria']

    def test_should_split_on_second_firstname(self):
        label_and_layout_line_list_list = [
            [
                ('<forename>', get_next_layout_line_for_text('John')),
                ('<surname>', get_next_layout_line_for_text('Smith')),
                ('<forename>', get_next_layout_line_for_text('Maria')),
                ('<surname>', get_next_layout_line_for_text('Madison'))
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
        nodes = tei_xpath(xml_root, AUTHOR_XPATH)
        assert len(nodes) == 2
        assert get_tei_xpath_text_content_list(
            nodes[0], './tei:forename'
        ) == ['John']
        assert get_tei_xpath_text_content_list(
            nodes[1], './tei:forename'
        ) == ['Maria']

    def test_should_not_create_person_name_for_note(self):
        label_and_layout_line_list_list = [
            [
                ('O', get_next_layout_line_for_text('before')),
                ('<forename>', get_next_layout_line_for_text('John')),
                ('<surname>', get_next_layout_line_for_text('Smith')),
                ('<marker>', get_next_layout_line_for_text('1')),
                ('O', get_next_layout_line_for_text(',')),
                ('<forename>', get_next_layout_line_for_text('Maria')),
                ('<surname>', get_next_layout_line_for_text('Madison')),
                ('<marker>', get_next_layout_line_for_text('2')),
                ('O', get_next_layout_line_for_text('after')),
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
        nodes = tei_xpath(xml_root, AUTHOR_XPATH)
        assert len(nodes) == 2
        assert get_tei_xpath_text_content_list(
            nodes[0], './tei:forename'
        ) == ['John']
        assert get_tei_xpath_text_content_list(
            nodes[1], './tei:forename'
        ) == ['Maria']
