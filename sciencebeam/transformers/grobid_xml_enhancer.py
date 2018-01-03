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

def get_logger():
  return logging.getLogger(__name__)

class GrobidXmlEnhancer(object):
  def __init__(self, grobid_url, start_service):
    self.process_header_names = grobid_service(
      grobid_url,
      GrobidApiPaths.PROCESS_HEADER_NAMES,
      start_service=start_service,
      field_name='names'
    )

  def __call__(self, extracted_xml):
    xml_root = etree.parse(BytesIO(extracted_xml))
    author_nodes = list(xml_root.findall(XmlPaths.AUTHOR))
    if author_nodes:
      authors = '\n'.join(x.text for x in author_nodes)
      get_logger().debug('authors: %s', authors)
      grobid_response = self.process_header_names(authors)
      get_logger().debug('grobid_response: %s', grobid_response)
      response_xml_root = etree.parse(BytesIO('<dummy>%s</dummy>' % grobid_response))
      for author in author_nodes:
        author.getparent().remove(author)
      author_parent_path, author_tag_name = rsplit_xml_path(XmlPaths.AUTHOR)
      for pers_name in response_xml_root.findall(TEI_PERS_NAME):
        get_logger().debug('pers_name: %s', pers_name)
        parent_node = create_node_recursive(xml_root, author_parent_path, exists_ok=True)
        node = E(author_tag_name)
        parent_node.append(node)
        for surname in pers_name.findall(TEI_SURNAME):
          node.append(E(JATS_SURNAME, surname.text))
        forenames = [x.text for x in pers_name.findall(TEI_FORNAME)]
        if forenames:
          node.append(E(JATS_GIVEN_NAMES, ' '.join(forenames)))
    return etree.tostring(xml_root, pretty_print=True)
