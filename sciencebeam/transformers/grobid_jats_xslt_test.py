import logging

import pytest

from lxml import etree
from lxml.builder import ElementMaker

from sciencebeam.transformers.xslt import xslt_transformer_from_file

LOGGER = logging.getLogger(__name__)

DEFAULT_GROBID_XSLT_PATH = 'xslt/grobid-jats.xsl'

E = ElementMaker(namespace='http://www.tei-c.org/ns/1.0')

VALUE_1 = 'value 1'
VALUE_2 = 'value 2'
VALUE_3 = 'value 3'

FIRST_NAME_1 = 'first name 1'
LAST_NAME_1 = 'last name 1'
EMAIL_1 = 'email@me.org'

FIRST_NAME_2 = 'first name 2'
LAST_NAME_2 = 'last name 2'
EMAIL_2 = 'email@you.org'

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

def _tei(titleStmt=None, biblStruct=None, authors=None):
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
  fileDesc.append(
    E.sourceDesc(
      biblStruct
    )
  )
  return E.TEI(
    E.teiHeader(
      fileDesc
    )
  )

def _author(forenames=None, surname=LAST_NAME_1, email=EMAIL_1, affiliation=None):
  if forenames is None:
    forenames = [FIRST_NAME_1]
  author = E.author()
  persName = E.persName()
  author.append(persName)
  for i, forename in enumerate(forenames):
    persName.append(E.forename(forename, type=('first' if i == 0 else 'middle')))
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
      assert _get_text(jats, 'front/journal-meta/journal-title-group/journal-title') == VALUE_1

    def test_should_not_add_journal_title_if_not_in_tei(self, grobid_jats_xslt):
      jats = etree.fromstring(grobid_jats_xslt(
        _tei()
      ))
      assert jats.xpath('front/journal-meta/journal-title-group/journal-title') == []

  class TestArticleTitle(object):
    def test_should_translate_title(self, grobid_jats_xslt):
      jats = etree.fromstring(grobid_jats_xslt(
        _tei(titleStmt=E.titleStmt(
          E.title(VALUE_1)
        ))
      ))
      assert _get_text(jats, 'front/article-meta/title-group/article-title') == VALUE_1

    def test_should_not_include_title_attributes_in_transformed_title_value(self, grobid_jats_xslt):
      jats = etree.fromstring(grobid_jats_xslt(
        _tei(titleStmt=E.titleStmt(
          E.title(VALUE_1, attrib1='other')
        ))
      ))
      assert _get_text(jats, 'front/article-meta/title-group/article-title') == VALUE_1

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
          _author(forenames=[FIRST_NAME_1], surname=LAST_NAME_1, email=EMAIL_1)
        ])
      ))
      person = _get_item(jats, 'front/article-meta/contrib-group/contrib')
      assert _get_text(person, './name/given-names') == FIRST_NAME_1
      assert _get_text(person, './name/surname') == LAST_NAME_1
      assert _get_text(person, './email') == EMAIL_1

    def test_should_not_add_email_if_not_in_tei(self, grobid_jats_xslt):
      jats = etree.fromstring(grobid_jats_xslt(
        _tei(authors=[
          _author(email=None)
        ])
      ))
      person = _get_item(jats, 'front/article-meta/contrib-group/contrib')
      assert person.xpath('./email') == []

    def test_should_add_contrib_type_person_attribute(self, grobid_jats_xslt):
      jats = etree.fromstring(grobid_jats_xslt(
        _tei(authors=[_author()])
      ))
      person = _get_item(jats, 'front/article-meta/contrib-group/contrib')
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
          _author(forenames=[FIRST_NAME_1], surname=LAST_NAME_1, email=EMAIL_1),
          _author(forenames=[FIRST_NAME_2], surname=LAST_NAME_2, email=EMAIL_2)
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

      person = _get_item(jats, 'front/article-meta/contrib-group/contrib')
      assert (
        _get_item(person, './xref[@ref-type="aff"]').attrib.get('rid') == AFFILIATION_1['key']
      )

      aff = _get_item(jats, 'front/article-meta/aff')
      assert aff.attrib.get('id') == AFFILIATION_1['key']
      assert (
        _get_text(aff, 'institution[@content-type="orgname"]') == AFFILIATION_1['institution']
      )
      assert (
        _get_text(aff, 'institution[@content-type="orgdiv1"]') == AFFILIATION_1['department']
      )
      assert (
        _get_text(aff, 'institution[@content-type="orgdiv2"]') == AFFILIATION_1['laboratory']
      )
      assert _get_text(aff, 'city') == AFFILIATION_1['city']
      assert _get_text(aff, 'country') == AFFILIATION_1['country']

    def test_should_not_add_affiliation_fields_not_in_tei(self, grobid_jats_xslt):
      jats = etree.fromstring(grobid_jats_xslt(
        _tei(authors=[
          _author(affiliation=_author_affiliation(key=AFFILIATION_1['key']))
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

      person = _get_item(jats, 'front/article-meta/contrib-group/contrib')
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
        _get_item(persons[0], './xref[@ref-type="aff"]').attrib.get('rid') == AFFILIATION_1['key']
      )
      assert (
        _get_item(persons[1], './xref[@ref-type="aff"]').attrib.get('rid') == AFFILIATION_2['key']
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
