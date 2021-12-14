import logging
from typing import Iterable

from lxml import etree

from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutLine
)
from sciencebeam_parser.document.tei.common import (
    get_tei_xpath_text_content_list,
    tei_xpath,
    TEI_NS_PREFIX
)
from sciencebeam_parser.models.data import (
    DEFAULT_DOCUMENT_FEATURES_CONTEXT,
    LayoutModelData
)
from sciencebeam_parser.models.citation.data import CitationDataGenerator
from sciencebeam_parser.models.citation.training_data import (
    CitationTeiTrainingDataGenerator
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


BIBL_XPATH = './tei:text/tei:back/tei:listBibl/tei:bibl'


def get_data_generator() -> CitationDataGenerator:
    return CitationDataGenerator(DEFAULT_DOCUMENT_FEATURES_CONTEXT)


def get_tei_training_data_generator() -> CitationTeiTrainingDataGenerator:
    return CitationTeiTrainingDataGenerator()


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
class TestCitationTeiTrainingDataGenerator:
    def test_should_include_layout_document_text_in_tei_output(self):
        layout_document = LayoutDocument.for_blocks([LayoutBlock.for_text(TEXT_1)])
        xml_root = get_training_tei_xml_for_layout_document(layout_document)
        assert xml_root.tag == TEI_NS_PREFIX + 'TEI'
        text_nodes = tei_xpath(xml_root, BIBL_XPATH)
        assert len(text_nodes) == 1
        assert get_text_content(text_nodes[0]).rstrip() == TEXT_1

    def test_should_keep_original_whitespace(self):
        text = 'Token1, Token2  ,Token3'
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(text, tail_whitespace='\n')
        ])])
        xml_root = get_training_tei_xml_for_layout_document(layout_document)
        text_nodes = tei_xpath(xml_root, BIBL_XPATH)
        assert len(text_nodes) == 1
        assert get_text_content(text_nodes[0]).rstrip() == text

    def test_should_add_line_feeds(self):
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = get_training_tei_xml_for_layout_document(layout_document)
        text_nodes = tei_xpath(xml_root, BIBL_XPATH)
        assert len(text_nodes) == 1
        assert get_text_content(text_nodes[0]).rstrip() == '\n'.join([TEXT_1, TEXT_2])

    def test_should_lb_elements_before_line_feeds(self):
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = get_training_tei_xml_for_layout_document(layout_document)
        text_nodes = tei_xpath(xml_root, BIBL_XPATH)
        assert len(text_nodes) == 1
        lb_nodes = tei_xpath(text_nodes[0], 'tei:lb')
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
        text_nodes = tei_xpath(xml_root, BIBL_XPATH)
        assert len(text_nodes) == 1
        lb_nodes = tei_xpath(text_nodes[0], 'tei:lb')
        assert len(lb_nodes) == 2
        assert lb_nodes[0].getparent().text == TEXT_1
        assert lb_nodes[0].tail == '\n' + TEXT_2

    def test_should_generate_tei_for_most_labels(self):
        label_and_layout_line_list = [
            ('<title>', get_next_layout_line_for_text('Title 1')),
            ('<author>', get_next_layout_line_for_text('Author 1')),
            ('<journal>', get_next_layout_line_for_text('Journal 1')),
            ('<series>', get_next_layout_line_for_text('Series 1')),
            ('<booktitle>', get_next_layout_line_for_text('Book Title 1')),
            ('<date>', get_next_layout_line_for_text('Date 1')),
            ('<volume>', get_next_layout_line_for_text('Volume 1')),
            ('<publisher>', get_next_layout_line_for_text('Publisher 1'))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        xml_root = get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        assert get_tei_xpath_text_content_list(
            xml_root, f'{BIBL_XPATH}/tei:title[@level="a"]'
        ) == ['Title 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{BIBL_XPATH}/tei:author'
        ) == ['Author 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{BIBL_XPATH}/tei:title[@level="j"]'
        ) == ['Journal 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{BIBL_XPATH}/tei:title[@level="s"]'
        ) == ['Series 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{BIBL_XPATH}/tei:title[@level="m"]'
        ) == ['Book Title 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{BIBL_XPATH}/tei:date'
        ) == ['Date 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{BIBL_XPATH}/tei:biblScope[@unit="volume"]'
        ) == ['Volume 1']
        assert get_tei_xpath_text_content_list(
            xml_root, f'{BIBL_XPATH}/tei:publisher'
        ) == ['Publisher 1']

    def test_should_map_other_label_as_text_without_note(self):
        label_and_layout_line_list = [
            ('<other>', get_next_layout_line_for_text(TEXT_1))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        training_data_generator = get_tei_training_data_generator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert not tei_xpath(xml_root, f'{BIBL_XPATH}//tei:note')
        assert get_tei_xpath_text_content_list(
            xml_root, BIBL_XPATH
        ) == [f'{TEXT_1}\n']

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
            xml_root, f'{BIBL_XPATH}/tei:note[@type="unknown"]'
        ) == [TEXT_1]

    def test_should_generate_tei_from_multiple_model_data_lists_using_model_labels(self):
        label_and_layout_line_list_list = [
            [
                ('<title>', get_next_layout_line_for_text(TEXT_1))
            ], [
                ('<title>', get_next_layout_line_for_text(TEXT_2))
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
        aff_nodes = tei_xpath(xml_root, BIBL_XPATH)
        assert len(aff_nodes) == 2
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:title[@level="a"]'
        ) == [TEXT_1]
        assert get_tei_xpath_text_content_list(
            aff_nodes[1], './tei:title[@level="a"]'
        ) == [TEXT_2]
