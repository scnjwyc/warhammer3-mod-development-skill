import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from model import Document, TAG, ATTR
from xml_format import format_xml
from hierarchy_edit import move
from test_hierarchy_edit import SOURCE
from xml_viewer import XMLViewer

class XMLFormatTests(unittest.TestCase):
 def test_format_idempotent_preserves_all_nodes_and_literal_values(self):
  for path in Path('examples').glob('*.xml'):
   source=path.read_text();formatted=format_xml(source)
   self.assertEqual(formatted,format_xml(formatted))
   def signature(s):return [(n.tag,n.attrs) for n in Document(s).nodes]
   self.assertEqual(signature(source),signature(formatted))
  source=SOURCE.replace('<components>','<!-- note -->\n<components>').replace('<a this="a"/>','<a this="a" expression="X &amp;&amp; Y < 2"/>')
  result=format_xml(source.replace('\n','\r\n'))
  self.assertIn('<!-- note -->',result)
  self.assertIn('X &amp;&amp; Y < 2',result)
  self.assertEqual(result,format_xml(result))
 def test_moves_do_not_accumulate_whitespace(self):
  source=format_xml(SOURCE)
  first=move(move(source,'a','c'),'a','r')
  for _ in range(30):source=move(move(source,'a','c'),'a','r')
  self.assertEqual(first,source)
  self.assertEqual(Document(source).parents['b'],'a')
 def test_preserve_definitions_on_move(self):
  source=format_xml(SOURCE)
  result=move(source,'a','c')
  self.assertEqual(source[source.index('<components>'):],result[result.index('<components>'):])
 def test_mixed_text_rejected_without_rewriting(self):
  with self.assertRaises(ValueError):format_xml(SOURCE.replace('<components>','<components>meaningful'))
 def test_search_direction_case_and_wrap(self):
  owner=SimpleNamespace(query=MagicMock(),case_sensitive=MagicMock(),text=MagicMock(),info=MagicMock(),source=SOURCE)
  owner.query.get.return_value='Root';owner.case_sensitive.get.return_value=True
  owner.text.tag_ranges.return_value=('3.0','3.4');owner.text.search.side_effect=['','1.0']
  XMLViewer.find(owner,True)
  calls=owner.text.search.call_args_list
  self.assertEqual(calls[0].args,('Root','3.0'))
  self.assertEqual(calls[1].args,('Root','end'))
  self.assertTrue(calls[0].kwargs['backwards']);self.assertFalse(calls[0].kwargs['nocase'])
  owner.case_sensitive.get.return_value=False;owner.text.search.side_effect=['4.0']
  XMLViewer.find(owner)
  self.assertEqual(owner.text.search.call_args.args,('Root','3.4'))
  self.assertTrue(owner.text.search.call_args.kwargs['nocase'])
