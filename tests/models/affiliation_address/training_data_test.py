import logging
from typing import Sequence

import pytest
from lxml import etree

from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutLine
)
from sciencebeam_parser.document.tei.common import (
    TEI_E,
    get_tei_xpath_text_content_list,
    tei_xpath
)
from sciencebeam_parser.models.data import (
    DEFAULT_DOCUMENT_FEATURES_CONTEXT
)
from sciencebeam_parser.models.affiliation_address.data import AffiliationAddressDataGenerator
from sciencebeam_parser.models.affiliation_address.training_data import (
    ROOT_TRAINING_XML_ELEMENT_PATH,
    TRAINING_XML_ELEMENT_PATH_BY_LABEL,
    AffiliationAddressTeiTrainingDataGenerator,
    AffiliationAddressTrainingTeiParser
)
from sciencebeam_parser.utils.xml_writer import XmlTreeWriter
from sciencebeam_parser.utils.xml import get_text_content

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


AFFILIATION_XPATH = (
    'tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:biblStruct'
    '/tei:analytic/tei:author/tei:affiliation'
)


def get_data_generator() -> AffiliationAddressDataGenerator:
    return AffiliationAddressDataGenerator(DEFAULT_DOCUMENT_FEATURES_CONTEXT)


def get_training_tei_parser() -> AffiliationAddressTrainingTeiParser:
    return AffiliationAddressTrainingTeiParser()


class TestAffiliationAddressTeiTrainingDataGenerator:
    def test_should_include_layout_document_text_in_tei_output(self):
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        layout_document = LayoutDocument.for_blocks([LayoutBlock.for_text(TEXT_1)])
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            get_model_data_list_for_layout_document(
                layout_document,
                data_generator=get_data_generator()
            )
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = tei_xpath(xml_root, AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_text_content(aff_nodes[0]).rstrip() == TEXT_1

    def test_should_keep_original_whitespace(self):
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        text = 'Token1, Token2  ,Token3'
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(text, tail_whitespace='\n')
        ])])
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            get_model_data_list_for_layout_document(
                layout_document,
                data_generator=get_data_generator()
            )
        )
        aff_nodes = tei_xpath(xml_root, AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_text_content(aff_nodes[0]).rstrip() == text

    def test_should_add_line_feeds(self):
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            get_model_data_list_for_layout_document(
                layout_document,
                data_generator=get_data_generator()
            )
        )
        aff_nodes = tei_xpath(xml_root, AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_text_content(aff_nodes[0]).rstrip() == '\n'.join([TEXT_1, TEXT_2])

    def test_should_lb_elements_before_line_feeds(self):
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[
            LayoutLine.for_text(TEXT_1, tail_whitespace='\n'),
            LayoutLine.for_text(TEXT_2, tail_whitespace='\n')
        ])])
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            get_model_data_list_for_layout_document(
                layout_document,
                data_generator=get_data_generator()
            )
        )
        aff_nodes = tei_xpath(xml_root, AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        lb_nodes = tei_xpath(aff_nodes[0], 'tei:lb')
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
        aff_nodes = tei_xpath(xml_root, AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        lb_nodes = tei_xpath(aff_nodes[0], 'tei:lb')
        assert len(lb_nodes) == 2
        assert lb_nodes[0].getparent().text == TEXT_1
        assert lb_nodes[0].tail == '\n' + TEXT_2

    def test_should_generate_tei_from_model_data_using_model_labels(self):
        label_and_layout_line_list = [
            ('<marker>', get_next_layout_line_for_text(TEXT_1)),
            ('<institution>', get_next_layout_line_for_text(TEXT_2))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = tei_xpath(xml_root, AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:marker'
        ) == [TEXT_1]
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:orgName[@type="institution"]'
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
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = tei_xpath(xml_root, AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:marker'
        ) == ['Marker 1']
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:orgName[@type="institution"]'
        ) == ['Institution 1']
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:orgName[@type="department"]'
        ) == ['Department 1']
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:orgName[@type="laboratory"]'
        ) == ['Laboratory 1']
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:address/tei:addrLine'
        ) == ['AddrLine 1']
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:address/tei:postCode'
        ) == ['PostCode 1']
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:address/tei:postBox'
        ) == ['PostBox 1']
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:address/tei:region'
        ) == ['Region 1']
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:address/tei:settlement'
        ) == ['Settlement 1']
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:address/tei:country'
        ) == ['Country 1']
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:address'
        ) == ['\n,\n'.join([
            'AddrLine 1', 'PostCode 1', 'PostBox 1', 'Region 1', 'Settlement 1', 'Country 1'
        ])]

    def test_should_map_unknown_label_to_note(self):
        label_and_layout_line_list = [
            ('<unknown>', get_next_layout_line_for_text(TEXT_1))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list,
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = tei_xpath(xml_root, AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:note[@type="unknown"]'
        ) == [TEXT_1]
        assert get_text_content(aff_nodes[0]) == f'{TEXT_1}\n'

    def test_should_not_join_separate_labels(self):
        label_and_layout_line_list = [
            ('<institution>', get_next_layout_line_for_text(TEXT_1)),
            ('<institution>', get_next_layout_line_for_text(TEXT_2))
        ]
        labeled_model_data_list = get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=get_data_generator()
        )
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_model_data_iterable(
            labeled_model_data_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = tei_xpath(xml_root, AFFILIATION_XPATH)
        assert len(aff_nodes) == 1
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:orgName[@type="institution"]'
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
            label_and_layout_line_list_list,
            data_generator=get_data_generator()
        )
        training_data_generator = AffiliationAddressTeiTrainingDataGenerator()
        xml_root = training_data_generator.get_training_tei_xml_for_multiple_model_data_iterables(
            labeled_model_data_list_list
        )
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        aff_nodes = tei_xpath(xml_root, AFFILIATION_XPATH)
        assert len(aff_nodes) == 2
        assert get_tei_xpath_text_content_list(
            aff_nodes[0], './tei:orgName[@type="institution"]'
        ) == [TEXT_1]
        assert get_tei_xpath_text_content_list(
            aff_nodes[1], './tei:orgName[@type="institution"]'
        ) == [TEXT_2]


def _get_training_tei_with_affiliations(
    affiliations: Sequence[etree.ElementBase]
) -> etree.ElementBase:
    xml_writer = XmlTreeWriter(TEI_E('TEI'), element_maker=TEI_E)
    xml_writer.require_path(
        ROOT_TRAINING_XML_ELEMENT_PATH[:-1]
    )
    xml_writer.append_all(*affiliations)
    LOGGER.debug('training tei: %r', etree.tostring(xml_writer.root))
    return xml_writer.root


class TestAffiliationAddressTrainingTeiParser:
    def test_should_parse_single_token_labelled_training_tei_lines(self):
        tei_root = _get_training_tei_with_affiliations([
            TEI_E('affiliation', *[
                TEI_E('orgName', {'type': 'institution'}, TOKEN_1, TEI_E('lb')),
                '\n',
                TEI_E('address', TEI_E('country', TOKEN_2, TEI_E('lb'))),
                '\n'
            ])
        ])
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        assert tag_result == [[
            (TOKEN_1, 'B-<institution>'),
            (TOKEN_2, 'B-<country>')
        ]]

    def test_should_parse_single_label_with_multiple_lines(self):
        tei_root = _get_training_tei_with_affiliations([
            TEI_E('affiliation', *[
                TEI_E(
                    'orgName',
                    {'type': 'institution'},
                    TOKEN_1,
                    TEI_E('lb'),
                    '\n',
                    TOKEN_2,
                    TEI_E('lb')
                ),
                '\n',
            ])
        ])
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        assert tag_result == [[
            (TOKEN_1, 'B-<institution>'),
            (TOKEN_2, 'I-<institution>')
        ]]

    def test_should_interpret_text_in_address_as_unlabelled(self):
        tei_root = _get_training_tei_with_affiliations([
            TEI_E('affiliation', *[
                TEI_E('address', TOKEN_1, TEI_E('lb')),
                '\n'
            ])
        ])
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        assert tag_result == [[
            (TOKEN_1, 'O')
        ]]

    def test_should_output_multiple_tokens_of_each_unlabelled_lines(self):
        tei_root = _get_training_tei_with_affiliations([
            TEI_E('affiliation', *[
                TOKEN_1,
                ' ',
                TOKEN_2,
                TEI_E('lb'),
                '\n',
                TOKEN_3,
                ' ',
                TOKEN_4,
                TEI_E('lb'),
                '\n'
            ])
        ])
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
        tei_root = _get_training_tei_with_affiliations([
            TEI_E('affiliation', *[
                TEI_E(
                    'orgName',
                    {'type': 'institution'},
                    TOKEN_1,
                    ' ',
                    TOKEN_2,
                    TEI_E('lb'),
                    '\n',
                    TOKEN_3,
                    ' ',
                    TOKEN_4,
                    TEI_E('lb')
                ),
                '\n',
            ])
        ])
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        LOGGER.debug('tag_result: %r', tag_result)
        assert tag_result == [[
            (TOKEN_1, 'B-<institution>'),
            (TOKEN_2, 'I-<institution>'),
            (TOKEN_3, 'I-<institution>'),
            (TOKEN_4, 'I-<institution>')
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
        xml_writer = XmlTreeWriter(TEI_E('tei'), element_maker=TEI_E)
        xml_writer.require_path(element_path)
        xml_writer.append_all(
            TOKEN_1,
            ' ',
            TOKEN_2,
            TEI_E('lb'),
            '\n',
            TOKEN_3,
            ' ',
            TOKEN_4,
            TEI_E('lb')
        )
        tei_root = xml_writer.root
        LOGGER.debug('tei_root: %r', etree.tostring(tei_root))
        tag_result = get_training_tei_parser().parse_training_tei_to_tag_result(
            tei_root
        )
        LOGGER.debug('tag_result: %r', tag_result)
        assert tag_result == [[
            (TOKEN_1, f'B-{tei_label}'),
            (TOKEN_2, f'I-{tei_label}'),
            (TOKEN_3, f'I-{tei_label}'),
            (TOKEN_4, f'I-{tei_label}')
        ]]
