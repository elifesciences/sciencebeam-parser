import logging
import json

import pytest

from lxml import etree

from sciencebeam_utils.utils.collection import extend_dict

from sciencebeam.transformers.xslt import xslt_transformer_from_file

from sciencebeam.transformers.json_to_xml import json_to_xml


LOGGER = logging.getLogger(__name__)

SCIENCEPARSE_XSLT_PATH = 'xslt/scienceparse-jats.xsl'

VALUE_1 = 'value 1'

FIRST_NAME_1 = 'FirstName1'
MIDDLE_NAME_1 = 'Middle1'
LAST_NAME_1 = 'LastName1'

FIRST_NAME_2 = 'FirstName2'
LAST_NAME_2 = 'LastName2'

AUTHOR_1 = {
    'first-name': FIRST_NAME_1,
    'last-name': LAST_NAME_1
}

AUTHOR_2 = {
    'first-name': FIRST_NAME_2,
    'last-name': LAST_NAME_2
}

ARTICLE_TITLE_1 = 'Article title 1'

REFERENCE_1 = {
    'title': ARTICLE_TITLE_1,
    'venue': 'Venue 1',
    'year': '2018'
}

HEADING_1 = 'Heading 1'
TEXT_1 = 'Text 1'

HEADING_2 = 'Heading 2'
TEXT_2 = 'Text 2'


@pytest.fixture(name='scienceparse_jats_xslt', scope='session')
def _scienceparse_jats_xslt():
    transformer = xslt_transformer_from_file(SCIENCEPARSE_XSLT_PATH)

    def wrapper(content):
        if isinstance(content, dict):
            xml = json_to_xml(json.dumps(content))
        else:
            raise ValueError('unsupported type: %s (%s)' % (
                type(content), content
            ))
        LOGGER.debug('input xml: %s', xml)
        output_xml = transformer(xml)
        LOGGER.debug('output xml: %s', output_xml)
        return output_xml
    return wrapper


def _get_item(xml, xpath):
    items = xml.xpath(xpath)
    if not items:
        raise AssertionError('xpath %s did not match any elements in xml %s' % (
            xpath, etree.tostring(xml)
        ))
    assert len(items) == 1
    return items[0]


def _get_text(xml, xpath):
    item = _get_item(xml, xpath)
    return item.text


class TestScienceParseJatsXslt:
    class TestArticleTitle:
        def test_should_translate_title(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'title': VALUE_1
            }))
            assert _get_text(
                jats, 'front/article-meta/title-group/article-title'
            ) == VALUE_1

        def test_should_not_add_title_if_not_in_json(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({}))
            assert jats.xpath(
                'front/article-meta/title-group/article-title'
            ) == []

    class TestAbstract:
        def test_should_translate_abstract(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'abstractText': VALUE_1
            }))
            assert _get_text(jats, 'front/article-meta/abstract') == VALUE_1

        def test_should_not_add_abstract_if_not_in_json(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({}))
            assert jats.xpath('front/article-meta/abstract') == []

    class TestAuthor:
        def test_should_translate_single_author_with_first_and_last_name(
                self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'authors': [{
                    'name': '%s %s' % (FIRST_NAME_1, LAST_NAME_1)
                }]
            }))
            person = _get_item(
                jats, 'front/article-meta/contrib-group/contrib'
            )
            assert _get_text(person, './name/given-names') == FIRST_NAME_1
            assert _get_text(person, './name/surname') == LAST_NAME_1

        def test_should_translate_single_author_with_middle_name(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'authors': [{
                    'name': '%s %s %s' % (FIRST_NAME_1, MIDDLE_NAME_1, LAST_NAME_1)
                }]
            }))
            person = _get_item(
                jats, 'front/article-meta/contrib-group/contrib'
            )
            assert _get_text(
                person, './name/given-names'
            ) == '%s %s' % (FIRST_NAME_1, MIDDLE_NAME_1)
            assert _get_text(person, './name/surname') == LAST_NAME_1

        def test_should_translate_single_author_with_last_name_only(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'authors': [{
                    'name': LAST_NAME_1
                }]
            }))
            person = _get_item(
                jats, 'front/article-meta/contrib-group/contrib'
            )
            assert _get_text(person, './name/surname') == LAST_NAME_1
            assert person.xpath('./name/given-names') == []

        def test_should_add_contrib_type_person_attribute(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'authors': [{
                    'name': '%s %s' % (FIRST_NAME_1, LAST_NAME_1)
                }]
            }))
            person = _get_item(
                jats, 'front/article-meta/contrib-group/contrib'
            )
            assert person.attrib.get('contrib-type') == 'person'

        def test_should_add_content_type_author_attribute_to_contrib_group(
                self, scienceparse_jats_xslt):

            jats = etree.fromstring(scienceparse_jats_xslt({
                'authors': [{
                    'name': '%s %s' % (FIRST_NAME_1, LAST_NAME_1)
                }]
            }))
            person = _get_item(jats, 'front/article-meta/contrib-group')
            assert person.attrib.get('content-type') == 'author'

        def test_should_translate_multiple_authors(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'authors': [{
                    'name': '%s %s' % (FIRST_NAME_1, LAST_NAME_1)
                }, {
                    'name': '%s %s' % (FIRST_NAME_2, LAST_NAME_2)
                }]
            }))
            persons = jats.xpath('front/article-meta/contrib-group/contrib')
            assert _get_text(persons[0], './name/surname') == LAST_NAME_1
            assert _get_text(persons[1], './name/surname') == LAST_NAME_2

    class TestBody:
        def test_should_add_body(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({}))
            assert _get_item(jats, 'body') is not None

    class TestBack:
        def test_should_add_back(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({}))
            assert _get_item(jats, 'back') is not None

    class TestReferences:
        def test_should_convert_single_reference(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'references': [
                    REFERENCE_1
                ]
            }))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')

            assert ref.attrib.get('id') == 'ref-1'
            assert element_citation.attrib.get('publication-type') == 'journal'
            assert _get_text(
                element_citation, 'article-title'
            ) == REFERENCE_1['title']
            assert _get_text(element_citation, 'year') == REFERENCE_1['year']

        def test_should_convert_venue_as_source(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'references': [
                    extend_dict(REFERENCE_1, {'venue': VALUE_1})
                ]
            }))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')

            assert _get_text(element_citation, 'source') == VALUE_1

        def test_should_convert_multiple_article_authors_of_single_reference(
                self, scienceparse_jats_xslt):

            authors = [AUTHOR_1, AUTHOR_2]
            jats = etree.fromstring(scienceparse_jats_xslt({
                'references': [
                    extend_dict(REFERENCE_1, {
                        'authors': [
                            {'name': '%s %s' % (
                                author['first-name'], author['last-name']
                            )}
                            for author in authors
                        ]
                    })
                ]
            }))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')
            person_group = _get_item(element_citation, 'person-group')
            persons = person_group.xpath('name')
            assert len(persons) == 2

            for person, author in zip(persons, authors):
                assert _get_text(person, 'surname') == author['last-name']
                assert _get_text(person, 'given-names') == author['first-name']

    class TestSections:
        def test_should_convert_section_with_heading(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'sections': [{
                    'heading': HEADING_1,
                    'text': TEXT_1
                }]
            }))

            sec = _get_item(jats, 'body/sec')

            assert _get_text(sec, 'title') == HEADING_1
            assert _get_text(sec, 'p') == TEXT_1

        def test_should_convert_section_without_heading(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'sections': [{
                    'text': TEXT_1
                }]
            }))

            sec = _get_item(jats, 'body/sec')

            assert sec.xpath('title') == []

        def test_should_convert_multiple_sections(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'sections': [{
                    'heading': HEADING_1,
                    'text': TEXT_1
                }, {
                    'heading': HEADING_2,
                    'text': TEXT_2
                }]
            }))

            sec_list = jats.xpath('body/sec')
            assert len(sec_list) == 2

            assert _get_text(sec_list[0], 'title') == HEADING_1
            assert _get_text(sec_list[0], 'p') == TEXT_1
            assert _get_text(sec_list[1], 'title') == HEADING_2
            assert _get_text(sec_list[1], 'p') == TEXT_2

        def test_should_add_section_ids(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'sections': [{
                    'heading': HEADING_1,
                    'text': TEXT_1
                }, {
                    'heading': HEADING_1,
                    'text': TEXT_1
                }]
            }))

            sec_list = jats.xpath('body/sec')
            assert len(sec_list) == 2

            assert [
                sec.attrib.get('id')
                for sec in sec_list
            ] == ['sec-1', 'sec-2']


class TestScienceParseV2JatsXslt:
    class TestArticleTitle:
        def test_should_translate_title(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'doc': {
                    'title': VALUE_1
                }
            }))
            assert _get_text(
                jats, 'front/article-meta/title-group/article-title'
            ) == VALUE_1

    class TestAuthor:
        def test_should_translate_multiple_authors(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'doc': {
                    'authors': [
                        '%s %s' % (FIRST_NAME_1, LAST_NAME_1),
                        '%s %s' % (FIRST_NAME_2, LAST_NAME_2)
                    ]
                }
            }))
            persons = jats.xpath('front/article-meta/contrib-group/contrib')
            assert _get_text(persons[0], './name/surname') == LAST_NAME_1
            assert _get_text(persons[1], './name/surname') == LAST_NAME_2

    class TestReferences:
        def test_should_convert_single_reference(self, scienceparse_jats_xslt):
            jats = etree.fromstring(scienceparse_jats_xslt({
                'doc': {
                    'bibs': [
                        REFERENCE_1
                    ]
                }
            }))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')

            assert ref.attrib.get('id') == 'ref-1'
            assert element_citation.attrib.get('publication-type') == 'journal'
            assert _get_text(
                element_citation,
                'article-title'
            ) == REFERENCE_1['title']
            assert _get_text(element_citation, 'year') == REFERENCE_1['year']

        def test_should_convert_multiple_article_authors_of_single_reference(
                self, scienceparse_jats_xslt):

            authors = [AUTHOR_1, AUTHOR_2]
            jats = etree.fromstring(scienceparse_jats_xslt({
                'references': [
                    extend_dict(REFERENCE_1, {
                        'authors': [
                            '%s %s' % (
                                author['first-name'],
                                author['last-name']
                            )
                            for author in authors
                        ]
                    })
                ]
            }))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')
            person_group = _get_item(element_citation, 'person-group')
            persons = person_group.xpath('name')
            assert len(persons) == 2

            for person, author in zip(persons, authors):
                assert _get_text(person, 'surname') == author['last-name']
                assert _get_text(person, 'given-names') == author['first-name']
