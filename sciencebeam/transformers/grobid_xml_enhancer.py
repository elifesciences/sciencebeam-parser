import logging
from io import BytesIO

from lxml import etree
from lxml.builder import E

from sciencebeam_gym.inference_model.extract_to_xml import (
  XmlPaths,
  create_node_recursive,
  rsplit_xml_path
)

from sciencebeam.transformers.grobid_service import (
  grobid_service,
  GrobidApiPaths
)

TEI_NS = 'http://www.tei-c.org/ns/1.0'
TEI_NS_PREFIX = '{%s}' % TEI_NS
TEI_PERS_NAME = TEI_NS_PREFIX + 'persName'
TEI_FORNAME = TEI_NS_PREFIX + 'forename'
TEI_SURNAME = TEI_NS_PREFIX + 'surname'

JATS_SURNAME = 'surname'
JATS_GIVEN_NAMES = 'given-names'
JATS_ADDR_LINE = 'addr-line'
JATS_NAMED_CONTENT = 'named-content'
JATS_INSTITUTION = 'institution'

def get_logger():
  return logging.getLogger(__name__)

def create_or_append(xml_root, path):
  parent_path, tag_name = rsplit_xml_path(path)
  parent_node = create_node_recursive(xml_root, parent_path, exists_ok=True)
  node = E(tag_name)
  parent_node.append(node)
  return node

class GrobidXmlEnhancer(object):
  def __init__(self, grobid_url, start_service):
    self.process_header_names = grobid_service(
      grobid_url,
      GrobidApiPaths.PROCESS_HEADER_NAMES,
      start_service=start_service,
      field_name='names'
    )
    self.process_affiliations = grobid_service(
      grobid_url,
      GrobidApiPaths.PROCESS_AFFILIATIONS,
      start_service=start_service,
      field_name='affiliations'
    )

  def process_and_replace_authors(self, xml_root):
    author_nodes = list(xml_root.findall(XmlPaths.AUTHOR))
    if author_nodes:
      authors = '\n'.join(x.text for x in author_nodes)
      get_logger().debug('authors: %s', authors)
      grobid_response = self.process_header_names(authors)
      get_logger().debug('grobid_response: %s', grobid_response)
      response_xml_root = etree.parse(BytesIO('<dummy>%s</dummy>' % grobid_response))
      for author in author_nodes:
        author.getparent().remove(author)
      for pers_name in response_xml_root.findall(TEI_PERS_NAME):
        get_logger().debug('pers_name: %s', pers_name)
        node = create_or_append(xml_root, XmlPaths.AUTHOR)
        for surname in pers_name.findall(TEI_SURNAME):
          node.append(E(JATS_SURNAME, surname.text))
        forenames = [x.text for x in pers_name.findall(TEI_FORNAME)]
        if forenames:
          node.append(E(JATS_GIVEN_NAMES, ' '.join(forenames)))
    return xml_root

  def process_and_replace_affiliations(self, xml_root):
    aff_nodes = list(xml_root.findall(XmlPaths.AUTHOR_AFF))
    if aff_nodes:
      affiliations = '\n'.join(x.text for x in aff_nodes)
      get_logger().debug('affiliations: %s', affiliations)
      grobid_response = self.process_affiliations(affiliations)
      get_logger().debug('grobid_response: %s', grobid_response)
      response_xml_root = etree.parse(BytesIO('<dummy>%s</dummy>' % grobid_response))
      for aff in aff_nodes:
        aff.getparent().remove(aff)
      for affiliation in response_xml_root.findall('affiliation'):
        get_logger().debug('affiliation: %s', affiliation)
        node = create_or_append(xml_root, XmlPaths.AUTHOR_AFF)
        for department in affiliation.xpath('./orgName[@type="department"]'):
          node.append(E(
            JATS_ADDR_LINE,
            E(
              JATS_NAMED_CONTENT,
              department.text,
              {
                'content-type': 'department'
              }
            )
          ))
        for institution in affiliation.xpath('./orgName[@type="institution"]'):
          node.append(E(
            JATS_INSTITUTION,
            institution.text
          ))

  def __call__(self, extracted_xml):
    xml_root = etree.parse(BytesIO(extracted_xml))
    self.process_and_replace_authors(xml_root)
    self.process_and_replace_affiliations(xml_root)
    return etree.tostring(xml_root, pretty_print=True)
