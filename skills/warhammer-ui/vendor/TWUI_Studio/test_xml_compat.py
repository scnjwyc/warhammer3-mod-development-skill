import unittest
import xml.etree.ElementTree as ET
from model import Document


def sample(value):
 return '<layout><hierarchy><root this="g"/></hierarchy><components><root this="g" id="root"><callback_with_context context_function_id=\''+value+'\'/></root></components></layout>'

class XmlCompatibilityTests(unittest.TestCase):
 def test_cco_operators_preserve_source_and_offsets(self):
  source=sample('A < 2 && B > 0 &not &custom;')
  doc=Document(source)
  self.assertEqual(doc.source,source)
  cb=doc.components[0].children[0]
  self.assertEqual(cb.get('context_function_id'),'A < 2 && B > 0 &not &custom;')
  changed=doc.patch([(doc.components[0],{'id':'edited'})])
  self.assertEqual(changed,source.replace('id="root"','id="edited"'))
  self.assertEqual(Document(changed).components[0].children[0].get('context_function_id'),cb.get('context_function_id'))
 def test_edit_escapes_once(self):
  doc=Document(sample('A && B'))
  cb=doc.components[0].children[0]
  edited=doc.patch([(cb,{'context_function_id':cb.get('context_function_id')+' < 3'})])
  ET.fromstring(edited)
  self.assertIn('A &amp;&amp; B &lt; 3',edited)
  self.assertEqual(Document(edited).components[0].children[0].get('context_function_id'),'A && B < 3')
 def test_entities_not_double_decoded(self):
  doc=Document(sample('&quot; &amp;&amp; &amp;lt; &#65; &#x42;'))
  self.assertEqual(doc.components[0].children[0].get('context_function_id'),'" && &lt; A B')
 def test_invalid_structure_still_fails(self):
  with self.assertRaises(ET.ParseError):Document(sample('A && B').replace('</components>','</wrong>'))
 def test_unescaped_text_not_silently_repaired(self):
  with self.assertRaises(ET.ParseError):Document(sample('ok').replace('</components>','bad & text</components>'))
 def test_comments_untouched(self):
  source=sample('A && B').replace('<components>','<!-- example & <tag> --><components>')
  self.assertEqual(Document(source).source,source)

if __name__=='__main__':unittest.main()
