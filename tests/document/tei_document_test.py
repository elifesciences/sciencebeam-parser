import logging

from lxml import etree

from pygrobid.document.tei_document import TeiDocument, TEI_NS_MAP


LOGGER = logging.getLogger(__name__)


class TestTeiDocument:
    def test_should_be_able_to_set_title(self):
        document = TeiDocument()
        document.set_title('test')
        LOGGER.debug('xml: %r', etree.tostring(document.root))
        nodes = document.root.xpath(
            '//tei:title[@level="a"][@type="main"]', namespaces=TEI_NS_MAP
        )
        assert [e.text for e in nodes] == ['test']

    def test_should_be_able_to_set_abstract(self):
        document = TeiDocument()
        document.set_abstract('test')
        LOGGER.debug('xml: %r', etree.tostring(document.root))
        nodes = document.root.xpath(
            '//tei:abstract/tei:p', namespaces=TEI_NS_MAP
        )
        assert [e.text for e in nodes] == ['test']
