import logging
from io import BytesIO
from contextlib import contextmanager
from mock import patch, Mock

from lxml import etree
from lxml.builder import E

from sciencebeam_gym.inference_model.extract_to_xml import (
  XmlPaths,
  create_xml_text
)

from sciencebeam.transformers.grobid_service import (
  GrobidApiPaths
)

import sciencebeam.transformers.grobid_xml_enhancer as grobid_xml_enhancer
from sciencebeam.transformers.grobid_xml_enhancer import (
  GrobidXmlEnhancer
)

GROBID_URL = 'http://localhost:8080/api'

TEXT_1 = 'text 1'
TEXT_2 = 'text 2'

FORENAME_1 = 'forename 1'
FORENAME_2 = 'forename 2'
SURNAME_1 = 'surname 1'
SURNAME_2 = 'surname 2'

DEPARTMENT_1 = 'department 1'
DEPARTMENT_2 = 'department 2'
INSTITUTION_1 = 'institution 1'
INSTITUTION_2 = 'institution 2'

DEPARTMENT_XPATH = './addr-line/named-content[@content-type="department"]'
INSTITUTION_XPATH = './institution'

def get_logger():
  return logging.getLogger(__name__)

def setup_module():
  logging.basicConfig(level='DEBUG')

def pers_name(*names):
  forenames = names[:-1]
  surname = names[-1]
  return (
    '<persName xmlns="http://www.tei-c.org/ns/1.0">'
    '  %s'
    '  <surname>%s</surname>'
    '</persName>'
  ) % (
    ' '.join(
      '<forename type="%s">%s</forename>' % (
        'first' if i == 0 else 'middle',
        forename
      )
      for i, forename in enumerate(forenames)
    ),
    surname
  )

def tei_affiliation(department=None, institution=None):
  affiliation = E.affiliation()
  if department:
    affiliation.append(E.orgName(department, type='department'))
  if institution:
    affiliation.append(E.orgName(institution, type='institution'))
  return etree.tostring(affiliation)

def get_text(node):
  if isinstance(node, list):
    return ''.join(get_text(x) for x in node)
  return node.text if node is not None else None

def get_child_text(node, name):
  return get_text(node.find(name))

@contextmanager
def patch_grobid_service():
  with patch.object(grobid_xml_enhancer, 'grobid_service') as grobid_service:
    process_header_names = Mock()
    process_affiliations = Mock()
    grobid_service.side_effect = [process_header_names, process_affiliations]
    yield process_header_names, process_affiliations

class TestGrobidXmlEnhancer(object):
  def test_should_initialise_grobid_service(self):
    with patch.object(grobid_xml_enhancer, 'grobid_service') as grobid_service:
      GrobidXmlEnhancer(GROBID_URL, start_service=False)
      grobid_service.assert_any_call(
        GROBID_URL, GrobidApiPaths.PROCESS_HEADER_NAMES, start_service=False, field_name='names'
      )
      grobid_service.assert_any_call(
        GROBID_URL, GrobidApiPaths.PROCESS_AFFILIATIONS, start_service=False,
        field_name='affiliations'
      )

  def test_should_convert_single_author(self):
    logging.basicConfig(level='DEBUG')
    with patch_grobid_service() as (process_header_names, process_affiliations):
      _ = process_affiliations
      process_header_names.return_value = pers_name(FORENAME_1, SURNAME_1)
      enhancer = GrobidXmlEnhancer(GROBID_URL, start_service=False)
      xml_root = E.article()
      create_xml_text(xml_root, XmlPaths.AUTHOR, TEXT_1)
      enhanced_xml = enhancer(etree.tostring(xml_root))
      get_logger().info('enhanced_xml: %s', enhanced_xml)
      enhanced_xml_root = etree.parse(BytesIO(enhanced_xml))
      authors = enhanced_xml_root.findall(XmlPaths.AUTHOR)
      assert [
        (get_child_text(author, 'given-names'), get_child_text(author, 'surname'))
        for author in authors
      ] == [(FORENAME_1, SURNAME_1)]

  def test_should_convert_single_affiliation(self):
    logging.basicConfig(level='DEBUG')
    with patch_grobid_service() as (process_header_names, process_affiliations):
      _ = process_header_names
      process_affiliations.return_value = tei_affiliation(
        department=DEPARTMENT_1,
        institution=INSTITUTION_1
      )
      enhancer = GrobidXmlEnhancer(GROBID_URL, start_service=False)
      xml_root = E.article()
      create_xml_text(xml_root, XmlPaths.AUTHOR_AFF, TEXT_1)
      enhanced_xml = enhancer(etree.tostring(xml_root))
      get_logger().info('enhanced_xml: %s', enhanced_xml)
      enhanced_xml_root = etree.parse(BytesIO(enhanced_xml))
      affiliations = enhanced_xml_root.findall(XmlPaths.AUTHOR_AFF)
      assert [
        get_text(x.xpath(DEPARTMENT_XPATH)) for x in affiliations
      ] == [DEPARTMENT_1]
      assert [
        get_text(x.xpath(INSTITUTION_XPATH)) for x in affiliations
      ] == [INSTITUTION_1]

  def test_should_convert_multiple_author(self):
    logging.basicConfig(level='DEBUG')
    with patch_grobid_service() as (process_header_names, process_affiliations):
      _ = process_affiliations
      process_header_names.return_value = (
        pers_name(FORENAME_1, SURNAME_1) +
        pers_name(FORENAME_2, SURNAME_2)
      )
      enhancer = GrobidXmlEnhancer(GROBID_URL, start_service=False)
      xml_root = E.article()
      create_xml_text(xml_root, XmlPaths.AUTHOR, TEXT_1)
      create_xml_text(xml_root, XmlPaths.AUTHOR, TEXT_2)
      enhanced_xml = enhancer(etree.tostring(xml_root))
      get_logger().info('enhanced_xml: %s', enhanced_xml)
      enhanced_xml_root = etree.parse(BytesIO(enhanced_xml))
      authors = enhanced_xml_root.findall(XmlPaths.AUTHOR)
      assert [
        (get_child_text(author, 'given-names'), get_child_text(author, 'surname'))
        for author in authors
      ] == [(FORENAME_1, SURNAME_1), (FORENAME_2, SURNAME_2)]

  def test_should_convert_multiple_affiliations(self):
    logging.basicConfig(level='DEBUG')
    with patch_grobid_service() as (process_header_names, process_affiliations):
      _ = process_header_names
      process_affiliations.return_value = (
        tei_affiliation(
          department=DEPARTMENT_1,
          institution=INSTITUTION_1
        ) +
        tei_affiliation(
          department=DEPARTMENT_2,
          institution=INSTITUTION_2
        )
      )
      enhancer = GrobidXmlEnhancer(GROBID_URL, start_service=False)
      xml_root = E.article()
      create_xml_text(xml_root, XmlPaths.AUTHOR_AFF, TEXT_1)
      enhanced_xml = enhancer(etree.tostring(xml_root))
      get_logger().info('enhanced_xml: %s', enhanced_xml)
      enhanced_xml_root = etree.parse(BytesIO(enhanced_xml))
      affiliations = enhanced_xml_root.findall(XmlPaths.AUTHOR_AFF)
      assert [
        get_text(x.xpath(DEPARTMENT_XPATH)) for x in affiliations
      ] == [DEPARTMENT_1, DEPARTMENT_2]
      assert [
        get_text(x.xpath(INSTITUTION_XPATH)) for x in affiliations
      ] == [INSTITUTION_1, INSTITUTION_2]

  def test_should_combine_multiple_forenames(self):
    logging.basicConfig(level='DEBUG')
    with patch_grobid_service() as (process_header_names, process_affiliations):
      _ = process_affiliations
      process_header_names.return_value = pers_name(
        FORENAME_1, FORENAME_2, SURNAME_1
      )
      enhancer = GrobidXmlEnhancer(GROBID_URL, start_service=False)
      xml_root = E.article()
      create_xml_text(xml_root, XmlPaths.AUTHOR, TEXT_1)
      enhanced_xml = enhancer(etree.tostring(xml_root))
      get_logger().info('enhanced_xml: %s', enhanced_xml)
      enhanced_xml_root = etree.parse(BytesIO(enhanced_xml))
      authors = enhanced_xml_root.findall(XmlPaths.AUTHOR)
      assert [
        (get_child_text(author, 'given-names'), get_child_text(author, 'surname'))
        for author in authors
      ] == [(' '.join([FORENAME_1, FORENAME_2]), SURNAME_1)]
