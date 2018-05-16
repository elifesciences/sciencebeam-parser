import json

from lxml import etree

from .json_to_xml import json_to_xml

KEY_1 = 'key1'
KEY_2 = 'key2'
STRING_VALUE_1 = 'value 1'
INT_VALUE_1 = 123

def normalize_xml_content(xml):
  return etree.tostring(
    etree.fromstring(xml)
  )

class TestJsonToXml(object):
  def test_should_convert_empty_json(self):
    assert normalize_xml_content(json_to_xml(r'{}')) == '<root/>'

  def test_should_convert_string_property(self):
    assert normalize_xml_content(json_to_xml(json.dumps({
      KEY_1: STRING_VALUE_1
    }))) == '<root><key1 type="str">%s</key1></root>' % STRING_VALUE_1

  def test_should_convert_json_bytes(self):
    assert normalize_xml_content(json_to_xml(json.dumps({
      KEY_1: STRING_VALUE_1
    }).encode('utf-8'))) == '<root><key1 type="str">%s</key1></root>' % STRING_VALUE_1

  def test_should_convert_int_property(self):
    assert normalize_xml_content(json_to_xml(json.dumps({
      KEY_1: INT_VALUE_1
    }))) == '<root><key1 type="int">%s</key1></root>' % INT_VALUE_1

  def test_should_convert_array_of_string_property(self):
    assert normalize_xml_content(json_to_xml(json.dumps({
      KEY_1: [STRING_VALUE_1]
    }))) == '<root><key1 type="list"><item type="str">%s</item></key1></root>' % STRING_VALUE_1

  def test_should_convert_array_of_object_property(self):
    assert normalize_xml_content(json_to_xml(json.dumps({
      KEY_1: [{
        KEY_2: STRING_VALUE_1
      }]
    }))) == (
      '<root><key1 type="list">'
      '<item type="dict"><key2 type="str">%s</key2></item>'
      '</key1></root>' % STRING_VALUE_1
    )
