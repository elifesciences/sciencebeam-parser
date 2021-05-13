from lxml import etree

from sciencebeam.transformers.xslt import _to_xslt_input


class TestToXsltInput:
    def test_should_tolerate_duplicate_ids(self):
        result: etree.ElementBase = _to_xslt_input(
            '''
            <xml>
            <item xml:id="id1">item 1</item>
            <item xml:id="id1">item 2</item>
            </xml>
            '''
        )
        items = result.findall('item')
        assert len(items) == 2
        assert [item.text for item in items] == ['item 1', 'item 2']
