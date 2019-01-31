import logging

import pytest

from lxml import etree
from lxml.builder import ElementMaker

from sciencebeam_utils.utils.collection import extend_dict

from sciencebeam.transformers.xslt import xslt_transformer_from_file

LOGGER = logging.getLogger(__name__)

DEFAULT_GROBID_XSLT_PATH = 'xslt/grobid-jats.xsl'

E = ElementMaker(namespace='http://www.tei-c.org/ns/1.0', nsmap={'xml': 'xml'})

VALUE_1 = 'value 1'
VALUE_2 = 'value 2'
VALUE_3 = 'value 3'

FIRST_NAME_1 = 'first name 1'
LAST_NAME_1 = 'last name 1'
EMAIL_1 = 'email@me.org'

FIRST_NAME_2 = 'first name 2'
LAST_NAME_2 = 'last name 2'
EMAIL_2 = 'email@you.org'

AUTHOR_1 = {
    'first-name': FIRST_NAME_1,
    'last-name': LAST_NAME_1
}

AUTHOR_2 = {
    'first-name': FIRST_NAME_2,
    'last-name': LAST_NAME_2
}

AFFILIATION_1 = {
    'key': 'aff1',
    'department': 'Department of Science',
    'laboratory': 'Data Lab',
    'institution': 'Institute 1',
    'city': 'New London',
    'country': 'Country 1'
}

AFFILIATION_2 = {
    'key': 'aff2',
    'department': 'Department 2',
    'laboratory': 'Lab 2',
    'institution': 'Institute 2',
    'city': 'New New London',
    'country': 'Country 2'
}

ARTICLE_TITLE_1 = 'Article title 1'
COLLECTION_TITLE_1 = 'Collection title 1'

REFERENCE_1 = {
    'id': 'b0',
    'article_title': ARTICLE_TITLE_1,
    'journal_title': 'Journal 1',
    'year': '2018',
    'doi': '10.1234/doi1',
    'volume': 'volume1',
    'issue': 'issue1'
}


def setup_module():
    logging.root.handlers = []
    logging.basicConfig(level='DEBUG')


@pytest.fixture(name='grobid_jats_xslt', scope='session')
def _grobid_jats_xslt():
    transformer = xslt_transformer_from_file(DEFAULT_GROBID_XSLT_PATH)

    def wrapper(xml):
        xml = etree.tostring(xml)
        LOGGER.debug('tei: %s', xml)
        return transformer(xml)
    return wrapper


def _tei(titleStmt=None, biblStruct=None, authors=None, references=None):
    if authors is None:
        authors = []
    fileDesc = E.fileDesc()
    if titleStmt is not None:
        fileDesc.append(titleStmt)
    if biblStruct is None:
        biblStruct = E.biblStruct(
            E.analytic(
                *authors
            )
        )
    back = E.back()
    if references is not None:
        back.append(
            E.div(
                E.listBibl(
                    *references
                )
            )
        )
    fileDesc.append(
        E.sourceDesc(
            biblStruct
        )
    )
    return E.TEI(
        E.teiHeader(
            fileDesc
        ),
        E.text(
            back
        )
    )


def _author(forenames=None, surname=LAST_NAME_1, email=EMAIL_1, affiliation=None):
    if forenames is None:
        forenames = [FIRST_NAME_1]
    author = E.author()
    persName = E.persName()
    author.append(persName)
    for i, forename in enumerate(forenames):
        persName.append(E.forename(forename, type=(
            'first' if i == 0 else 'middle'
        )))
    if surname:
        persName.append(E.surname(surname))
    if email:
        author.append(E.email(email))
    if affiliation is not None:
        author.append(affiliation)
    return author


def _author_affiliation(**kwargs):
    props = kwargs
    affiliation = E.affiliation()
    if 'key' in props:
        affiliation.attrib['key'] = props['key']
    if 'department' in props:
        affiliation.append(E.orgName(props['department'], type='department'))
    if 'laboratory' in props:
        affiliation.append(E.orgName(props['laboratory'], type='laboratory'))
    if 'institution' in props:
        affiliation.append(E.orgName(props['institution'], type='institution'))
    address = E.address()
    affiliation.append(address)
    if 'city' in props:
        address.append(E.settlement(props['city']))
    if 'country' in props:
        address.append(E.country(props['country']))
    return affiliation


def _reference(**kwargs):
    props = kwargs
    bibl_struct = E.biblStruct()
    if 'id' in props:
        bibl_struct.attrib['{xml}id'] = props['id']

    analytic = E.analytic()
    bibl_struct.append(analytic)
    monogr = E.monogr()
    bibl_struct.append(monogr)
    imprint = E.imprint()
    monogr.append(imprint)

    title_level = props.get('title_level', 'a')
    if props.get('article_title') is not None:
        analytic.append(
            E.title(props['article_title'], level=title_level, type='main')
        )
    if 'collection_title' in props:
        monogr.append(
            E.title(props['collection_title'], level=title_level, type='main')
        )
    if 'journal_title' in props:
        monogr.append(E.title(props['journal_title'], level='j'))
    if 'year' in props:
        when = props['year']
        if 'month' in props:
            when += '-%s' % props['month']
            if 'day' in props:
                when += '-%s' % props['day']
        imprint.append(E.date(type='published', when=when))
    if 'volume' in props:
        imprint.append(E.biblScope(props['volume'], unit='volume'))
    if 'issue' in props:
        imprint.append(E.biblScope(props['issue'], unit='issue'))
    if 'fpage' in props and 'lpage' in props:
        imprint.append(E.biblScope(
            {'unit': 'page', 'from': props['fpage'], 'to': props['lpage']}
        ))
    if 'page' in props:
        imprint.append(E.biblScope(props['page'], unit='page'))
    if 'doi' in props:
        monogr.append(E.idno(props['doi'], type='doi'))
    if 'article_authors' in props:
        for author in props['article_authors']:
            analytic.append(_author(
                forenames=[author['first-name']],
                surname=author['last-name'],
                email=None
            ))
    if 'collection_authors' in props:
        for author in props['collection_authors']:
            monogr.append(_author(
                forenames=[author['first-name']],
                surname=author['last-name'],
                email=None
            ))
    return bibl_struct


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


class TestGrobidJatsXslt(object):
    class TestJournalTitle(object):
        def test_should_translate_journal_title(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(biblStruct=E.biblStruct(E.monogr(
                    E.title(VALUE_1)
                )))
            ))
            assert _get_text(
                jats, 'front/journal-meta/journal-title-group/journal-title'
            ) == VALUE_1

        def test_should_not_add_journal_title_if_not_in_tei(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei()
            ))
            assert jats.xpath(
                'front/journal-meta/journal-title-group/journal-title'
            ) == []

    class TestArticleTitle(object):
        def test_should_translate_title(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(titleStmt=E.titleStmt(
                    E.title(VALUE_1)
                ))
            ))
            assert _get_text(
                jats, 'front/article-meta/title-group/article-title'
            ) == VALUE_1

        def test_should_not_include_title_attributes_in_transformed_title_value(
                self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(titleStmt=E.titleStmt(
                    E.title(VALUE_1, attrib1='other')
                ))
            ))
            assert _get_text(
                jats, 'front/article-meta/title-group/article-title'
            ) == VALUE_1

        def test_should_include_values_of_sub_elements(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(titleStmt=E.titleStmt(
                    E.title(
                        E.before(VALUE_1),
                        VALUE_2,
                        E.after(VALUE_3)
                    )
                ))
            ))
            assert (
                _get_text(jats, 'front/article-meta/title-group/article-title') ==
                ''.join([VALUE_1, VALUE_2, VALUE_3])
            )

    class TestAuthor(object):
        def test_should_translate_single_author(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(authors=[
                    _author(
                        forenames=[FIRST_NAME_1],
                        surname=LAST_NAME_1,
                        email=EMAIL_1
                    )
                ])
            ))
            person = _get_item(
                jats, 'front/article-meta/contrib-group/contrib'
            )
            assert _get_text(person, './name/given-names') == FIRST_NAME_1
            assert _get_text(person, './name/surname') == LAST_NAME_1
            assert _get_text(person, './email') == EMAIL_1

        def test_should_include_middle_name_in_given_names(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(authors=[
                    _author(
                        forenames=[FIRST_NAME_1, FIRST_NAME_2],
                        surname=LAST_NAME_1,
                        email=EMAIL_1
                    )
                ])
            ))
            person = _get_item(
                jats, 'front/article-meta/contrib-group/contrib'
            )
            assert _get_text(
                person, './name/given-names'
            ) == '%s %s' % (FIRST_NAME_1, FIRST_NAME_2)

        def test_should_not_add_email_if_not_in_tei(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(authors=[
                    _author(email=None)
                ])
            ))
            person = _get_item(
                jats, 'front/article-meta/contrib-group/contrib'
            )
            assert person.xpath('./email') == []

        def test_should_add_contrib_type_person_attribute(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(authors=[_author()])
            ))
            person = _get_item(
                jats, 'front/article-meta/contrib-group/contrib'
            )
            assert person.attrib.get('contrib-type') == 'person'

        def test_should_add_content_type_author_attribute_to_contrib_group(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(authors=[_author()])
            ))
            person = _get_item(jats, 'front/article-meta/contrib-group')
            assert person.attrib.get('content-type') == 'author'

        def test_should_translate_multiple_authors(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(authors=[
                    _author(
                        forenames=[FIRST_NAME_1],
                        surname=LAST_NAME_1,
                        email=EMAIL_1
                    ),
                    _author(
                        forenames=[FIRST_NAME_2],
                        surname=LAST_NAME_2,
                        email=EMAIL_2
                    )
                ])
            ))
            persons = jats.xpath('front/article-meta/contrib-group/contrib')
            assert _get_text(persons[0], './name/surname') == LAST_NAME_1
            assert _get_text(persons[1], './name/surname') == LAST_NAME_2

    class TestAuthorAffiliation(object):
        def test_should_add_affiliation_of_single_author_with_xref(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(authors=[
                    _author(affiliation=_author_affiliation(**AFFILIATION_1))
                ])
            ))

            person = _get_item(
                jats, 'front/article-meta/contrib-group/contrib'
            )
            assert (
                _get_item(
                    person, './xref[@ref-type="aff"]'
                ).attrib.get('rid') == AFFILIATION_1['key']
            )

            aff = _get_item(jats, 'front/article-meta/aff')
            assert aff.attrib.get('id') == AFFILIATION_1['key']
            assert (
                _get_text(
                    aff, 'institution[@content-type="orgname"]'
                ) == AFFILIATION_1['institution']
            )
            assert (
                _get_text(
                    aff, 'institution[@content-type="orgdiv1"]'
                ) == AFFILIATION_1['department']
            )
            assert (
                _get_text(
                    aff, 'institution[@content-type="orgdiv2"]'
                ) == AFFILIATION_1['laboratory']
            )
            assert _get_text(aff, 'city') == AFFILIATION_1['city']
            assert _get_text(aff, 'country') == AFFILIATION_1['country']

        def test_should_not_add_affiliation_fields_not_in_tei(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(authors=[
                    _author(affiliation=_author_affiliation(
                        key=AFFILIATION_1['key']
                    ))
                ])
            ))

            aff = _get_item(jats, 'front/article-meta/aff')
            assert aff.xpath('institution[@content-type="orgname"]') == []
            assert aff.xpath('institution[@content-type="orgdiv1"]') == []
            assert aff.xpath('institution[@content-type="orgdiv2"]') == []
            assert aff.xpath('city') == []
            assert aff.xpath('country') == []

        def test_should_not_add_affiliation_if_not_in_tei(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(authors=[_author()])
            ))

            person = _get_item(
                jats, 'front/article-meta/contrib-group/contrib'
            )
            assert person.xpath('./xref[@ref-type="aff"]') == []

            assert jats.xpath('front/article-meta/aff') == []

        def test_should_add_multiple_affiliations(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(authors=[
                    _author(affiliation=_author_affiliation(**AFFILIATION_1)),
                    _author(affiliation=_author_affiliation(**AFFILIATION_2))
                ])
            ))

            persons = jats.xpath('front/article-meta/contrib-group/contrib')
            assert (
                _get_item(
                    persons[0], './xref[@ref-type="aff"]'
                ).attrib.get('rid') == AFFILIATION_1['key']
            )
            assert (
                _get_item(
                    persons[1], './xref[@ref-type="aff"]'
                ).attrib.get('rid') == AFFILIATION_2['key']
            )

            affs = jats.xpath('front/article-meta/aff')
            assert affs[0].attrib.get('id') == AFFILIATION_1['key']
            assert affs[1].attrib.get('id') == AFFILIATION_2['key']

    class TestBody(object):
        def test_should_add_body(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei()
            ))
            assert _get_item(jats, 'body') is not None

    class TestBack(object):
        def test_should_add_back(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei()
            ))
            assert _get_item(jats, 'back') is not None

    class TestReferences(object):
        def test_should_convert_single_reference(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(references=[_reference(**REFERENCE_1)])
            ))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')

            assert ref.attrib.get('id') == REFERENCE_1['id']
            assert element_citation.attrib.get('publication-type') == 'journal'
            assert _get_text(
                element_citation,
                'article-title'
            ) == REFERENCE_1['article_title']
            assert _get_text(element_citation, 'year') == REFERENCE_1['year']
            assert _get_text(
                element_citation, 'source'
            ) == REFERENCE_1['journal_title']
            assert _get_text(
                element_citation, 'volume'
            ) == REFERENCE_1['volume']
            assert _get_text(element_citation, 'issue') == REFERENCE_1['issue']
            assert _get_text(
                element_citation, 'pub-id[@pub-id-type="doi"]'
            ) == REFERENCE_1['doi']

        def test_should_fallback_to_collection_title_if_article_title_does_not_exist(
                self, grobid_jats_xslt):

            jats = etree.fromstring(grobid_jats_xslt(
                _tei(references=[_reference(**extend_dict(
                    REFERENCE_1, article_title=None, collection_title=COLLECTION_TITLE_1
                ))])
            ))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')

            assert _get_text(
                element_citation, 'article-title'
            ) == COLLECTION_TITLE_1

        def test_should_only_return_article_title_even_if_collection_title_exists(
                self, grobid_jats_xslt):

            jats = etree.fromstring(grobid_jats_xslt(
                _tei(references=[_reference(**extend_dict(
                    REFERENCE_1, article_title=ARTICLE_TITLE_1, collection_title=COLLECTION_TITLE_1
                ))])
            ))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')

            assert _get_text(
                element_citation,
                'article-title'
            ) == ARTICLE_TITLE_1

        @pytest.mark.parametrize('title_level', ['a', 'm'])
        def test_should_only_return_article_title_at_different_levels(
                self, grobid_jats_xslt, title_level):

            jats = etree.fromstring(grobid_jats_xslt(
                _tei(references=[_reference(**extend_dict(
                    REFERENCE_1, article_title=ARTICLE_TITLE_1, title_level=title_level
                ))])
            ))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')

            assert _get_text(
                element_citation, 'article-title'
            ) == ARTICLE_TITLE_1

        def test_should_convert_page_range(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(references=[_reference(**extend_dict(
                    REFERENCE_1, fpage='fpage', lpage='lpage'
                ))])
            ))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')

            assert _get_text(element_citation, 'fpage') == 'fpage'
            assert _get_text(element_citation, 'lpage') == 'lpage'

        def test_should_convert_single_page_no(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(references=[_reference(**extend_dict(
                    REFERENCE_1, page='page1'
                ))])
            ))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')

            assert _get_text(element_citation, 'fpage') == 'page1'
            assert _get_text(element_citation, 'lpage') == 'page1'

        def test_should_convert_year_and_month(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(references=[_reference(**extend_dict(
                    REFERENCE_1, year='2001', month='02'
                ))])
            ))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')

            assert _get_text(element_citation, 'year') == '2001'
            assert _get_text(element_citation, 'month') == '02'

        def test_should_convert_year_month_and_day(self, grobid_jats_xslt):
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(references=[_reference(**extend_dict(
                    REFERENCE_1, year='2001', month='02', day='03'
                ))])
            ))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')

            assert _get_text(element_citation, 'year') == '2001'
            assert _get_text(element_citation, 'month') == '02'
            assert _get_text(element_citation, 'day') == '03'

        def test_should_convert_multiple_article_authors_of_single_reference(
                self, grobid_jats_xslt):
            authors = [AUTHOR_1, AUTHOR_2]
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(references=[
                    _reference(**extend_dict(
                        REFERENCE_1,
                        article_authors=authors
                    ))
                ])
            ))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')
            person_group = _get_item(element_citation, 'person-group')
            persons = person_group.xpath('name')
            assert len(persons) == 2

            for person, author in zip(persons, authors):
                assert _get_text(person, 'surname') == author['last-name']
                assert _get_text(person, 'given-names') == author['first-name']

        def test_should_convert_multiple_collection_authors_of_single_reference(
                self, grobid_jats_xslt):
            authors = [AUTHOR_1, AUTHOR_2]
            jats = etree.fromstring(grobid_jats_xslt(
                _tei(references=[
                    _reference(**extend_dict(
                        REFERENCE_1,
                        collection_authors=authors
                    ))
                ])
            ))

            ref_list = _get_item(jats, 'back/ref-list')
            ref = _get_item(ref_list, 'ref')
            element_citation = _get_item(ref, 'element-citation')
            person_group = _get_item(element_citation, 'person-group')
            persons = person_group.xpath('name')
            assert len(persons) == 2

            for person, author in zip(persons, authors):
                assert _get_text(person, 'surname') == author['last-name']
                assert _get_text(person, 'given-names') == author['first-name']
