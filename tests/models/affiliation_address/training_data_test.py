import logging
from typing import Sequence, Tuple

from lxml import etree

from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutLine,
    LayoutLineDescriptor
)
from sciencebeam_parser.models.data import (
    DEFAULT_DOCUMENT_FEATURES_CONTEXT,
    LabeledLayoutModelData,
    LayoutModelData
)
from sciencebeam_parser.models.affiliation_address.data import AffiliationAddressDataGenerator
from sciencebeam_parser.models.affiliation_address.training_data import (
    AffiliationAddressTeiTrainingDataGenerator
)
from sciencebeam_parser.utils.xml import get_text_content, get_text_content_list


LOGGER = logging.getLogger(__name__)


TEXT_1 = 'this is text 1'
TEXT_2 = 'this is text 2'


AFFILIATION_XPATH = (
    'teiHeader/fileDesc/sourceDesc/biblStruct/analytic/author/affiliation'
)


def get_data_generator() -> AffiliationAddressDataGenerator:
    return AffiliationAddressDataGenerator(DEFAULT_DOCUMENT_FEATURES_CONTEXT)


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


class TestAffiliationAddressTeiTrainingDataGenerator:
    def test_should_include_layout_document_text_in_tei_output(self):
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        layout_document = LayoutDocument.for_blocks([LayoutBlock.for_text(TEXT_1)])
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            get_model_data_list_for_layout_document(layout_document)
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = xml_root.xpath(AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_text_content(aff_nodes[0]).rstrip() == TEXT_1

    def test_should_add_line_feeds(self):
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            get_model_data_list_for_layout_document(layout_document)
        )
        aff_nodes = xml_root.xpath(AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_text_content(aff_nodes[0]).rstrip() == '\n'.join([TEXT_1, TEXT_2])

    def test_should_lb_elements_before_line_feeds(self):
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            get_model_data_list_for_layout_document(layout_document)
        )
        aff_nodes = xml_root.xpath(AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        lb_nodes = aff_nodes[0].xpath('lb')
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
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            model_data_iterable
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = xml_root.xpath(AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        lb_nodes = aff_nodes[0].xpath('lb')
        assert len(lb_nodes) == 2
        assert lb_nodes[0].getparent().text == TEXT_1
        assert lb_nodes[0].tail == '\n' + TEXT_2

    def test_should_generate_tei_from_model_data_using_model_labels(self):
        label_and_layout_line_list = [
            ('<marker>', get_next_layout_line_for_text(TEXT_1)),
            ('<institution>', get_next_layout_line_for_text(TEXT_2))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list
        )
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = xml_root.xpath(AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_text_content_list(
            aff_nodes[0].xpath('./marker')
        ) == [TEXT_1]
        assert get_text_content_list(
            aff_nodes[0].xpath('./orgName[@type="institution"]')
        ) == [TEXT_2]
        assert get_text_content(aff_nodes[0]) == f'{TEXT_1}\n{TEXT_2}\n'

    def test_should_generate_tei_for_most_labels(self):
        label_and_layout_line_list = [
            ('<marker>', get_next_layout_line_for_text('Marker 1')),
            ('<institution>', get_next_layout_line_for_text('Institution 1')),
            ('<department>', get_next_layout_line_for_text('Department 1')),
            ('<laboratory>', get_next_layout_line_for_text('Laboratory 1')),
            ('<addrLine>', get_next_layout_line_for_text('AddrLine 1')),
            ('O', get_next_layout_line_for_text(',')),
            ('<postCode>', get_next_layout_line_for_text('PostCode 1')),
            ('O', get_next_layout_line_for_text(',')),
            ('<postBox>', get_next_layout_line_for_text('PostBox 1')),
            ('O', get_next_layout_line_for_text(',')),
            ('<region>', get_next_layout_line_for_text('Region 1')),
            ('O', get_next_layout_line_for_text(',')),
            ('<settlement>', get_next_layout_line_for_text('Settlement 1')),
            ('O', get_next_layout_line_for_text(',')),
            ('<country>', get_next_layout_line_for_text('Country 1'))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list
        )
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = xml_root.xpath(AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_text_content_list(
            aff_nodes[0].xpath('./marker')
        ) == ['Marker 1']
        assert get_text_content_list(
            aff_nodes[0].xpath('./orgName[@type="institution"]')
        ) == ['Institution 1']
        assert get_text_content_list(
            aff_nodes[0].xpath('./orgName[@type="department"]')
        ) == ['Department 1']
        assert get_text_content_list(
            aff_nodes[0].xpath('./orgName[@type="laboratory"]')
        ) == ['Laboratory 1']
        assert get_text_content_list(
            aff_nodes[0].xpath('./address/addrLine')
        ) == ['AddrLine 1']
        assert get_text_content_list(
            aff_nodes[0].xpath('./address/postCode')
        ) == ['PostCode 1']
        assert get_text_content_list(
            aff_nodes[0].xpath('./address/postBox')
        ) == ['PostBox 1']
        assert get_text_content_list(
            aff_nodes[0].xpath('./address/region')
        ) == ['Region 1']
        assert get_text_content_list(
            aff_nodes[0].xpath('./address/settlement')
        ) == ['Settlement 1']
        assert get_text_content_list(
            aff_nodes[0].xpath('./address/country')
        ) == ['Country 1']
        assert get_text_content_list(
            aff_nodes[0].xpath('./address')
        ) == ['\n,\n'.join([
            'AddrLine 1', 'PostCode 1', 'PostBox 1', 'Region 1', 'Settlement 1', 'Country 1'
        ])]

    def test_should_map_unknown_label_to_note(self):
        label_and_layout_line_list = [
            ('<unknown>', get_next_layout_line_for_text(TEXT_1))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list
        )
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = xml_root.xpath(AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_text_content_list(
            aff_nodes[0].xpath('./note[@type="unknown"]')
        ) == [TEXT_1]
        assert get_text_content(aff_nodes[0]) == f'{TEXT_1}\n'

    def test_should_not_join_separate_labels(self):
        label_and_layout_line_list = [
            ('<institution>', get_next_layout_line_for_text(TEXT_1)),
            ('<institution>', get_next_layout_line_for_text(TEXT_2))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list
        )
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = xml_root.xpath(AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_text_content_list(
            aff_nodes[0].xpath('./orgName[@type="institution"]')
        ) == [TEXT_1, TEXT_2]
        assert get_text_content(aff_nodes[0]) == f'{TEXT_1}\n{TEXT_2}\n'

    def test_should_generate_tei_from_multiple_model_data_lists_using_model_labels(self):
        label_and_layout_line_list_list = [
            [
                ('<institution>', get_next_layout_line_for_text(TEXT_1))
            ], [
                ('<institution>', get_next_layout_line_for_text(TEXT_2))
            ]
        ]
        labeled_model_data_list_list = get_labeled_model_data_list_list(
            label_and_layout_line_list_list
        )
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_multiple_model_data_iterables(
            labeled_model_data_list_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = xml_root.xpath(AFFILIATION_XPATH)
        assert len(aff_nodes) == 2
        assert get_text_content_list(
            aff_nodes[0].xpath('./orgName[@type="institution"]')
        ) == [TEXT_1]
        assert get_text_content_list(
            aff_nodes[1].xpath('./orgName[@type="institution"]')
        ) == [TEXT_2]
