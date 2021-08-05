from pathlib import Path

from lxml import etree
from lxml.builder import ElementMaker

from sciencebeam_parser.lookup import SimpleTextLookUp
from sciencebeam_parser.lookup.xml_lookup import load_xml_lookup_from_file


TEI_NS = 'http://www.tei-c.org/ns/1.0'
TEI_NS_PREFIX = '{%s}' % TEI_NS

TEI_NS_MAP = {
    'tei': TEI_NS
}

TEI_E = ElementMaker(namespace=TEI_NS, nsmap={
    None: TEI_NS
})


class TestLoadXmlCountryLookupFromFile:
    def test_should_load_simple_xml_files(self, tmp_path: Path):
        country_xml_file = tmp_path / 'country.xml'
        country_xml_file.write_bytes(etree.tostring(TEI_E.TEI(
            TEI_E.text(TEI_E.body(TEI_E.div(TEI_E.table(
                TEI_E.row(
                    TEI_E.cell({'role': 'a2code'}, 'GB'),
                    TEI_E.cell({'role': 'a3code'}, 'GBR'),
                    TEI_E.cell({'role': 'name'}, 'UNITED KINGDOM'),
                    TEI_E.cell({'role': 'name'}, 'UK')
                )
            ))))
        )))
        country_lookup = load_xml_lookup_from_file(str(country_xml_file))
        assert isinstance(country_lookup, SimpleTextLookUp)
        assert country_lookup.contains('OTHER') is False
        assert country_lookup.contains('GB') is True
        assert country_lookup.contains('GBR') is True
        assert country_lookup.contains('UK') is True
        assert country_lookup.contains('uk') is True
