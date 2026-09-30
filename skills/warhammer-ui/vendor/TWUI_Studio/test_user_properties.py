import unittest
from model import Document
from user_properties import property_values,apply_user_properties
from test_view_state import XML
import test_view_state

class PropertyTests(unittest.TestCase):
 def test_add_edit_remove_roundtrip(self):
  original=XML;source=apply_user_properties(original,'p',{'dynamic_child':'1','dynamic_child_parent':'button & "name"'})
  self.assertLess(source.index('<userproperties>'),source.index('<states>',source.index('<parent this="p" id=')))
  d=Document(source);self.assertEqual(property_values(d.by_guid['p']),{'dynamic_child':'1','dynamic_child_parent':'button & "name"'})
  self.assertEqual(apply_user_properties(source,'p',property_values(d.by_guid['p'])),source)
  source=apply_user_properties(source,'p',{'dynamic_child':'0'})
  self.assertEqual(property_values(Document(source).by_guid['p']),{'dynamic_child':'0'})
  source=apply_user_properties(source,'p',{});self.assertIsNone(Document(source).by_guid['p'].child('userproperties'))
 def test_unrelated_data_preserved(self):
  source=apply_user_properties(XML,'p',{'custom':'x'})
  source=source.replace('name="custom"','extra="keep" name="custom"').replace('value="x"','value="x"/><!-- keep --><other value="data"')
  changed=apply_user_properties(source,'p',{'custom':'y','new':'z'})
  self.assertIn('extra="keep"',changed);self.assertIn('<!-- keep -->',changed);self.assertIn('<other value="data"',changed)
 def test_self_closing_component(self):
  source=XML.replace('<child this="c" id="child" offset="12,15"><states><s width="20" height="10"/></states></child>','<child this="c" id="child"/>')
  self.assertEqual(property_values(Document(apply_user_properties(source,'c',{'a':'b'})).by_guid['c']),{'a':'b'})

class IsolationExtensionTests(unittest.TestCase):
 def setUp(self):test_view_state.ViewTests.setUp(self)
 def test_add_other_subtree_then_hide_and_undo(self):
  a=self.a;a.tree.selection.return_value=('c',);a.view_action('only');a.tree.selection.return_value=('o',)
  a.view_action('toggle');self.assertEqual(set(a.focus_guid),{'c','o'})
  a.history_travel();self.assertEqual(set(a.focus_guid),{'c'})
  a.history_travel(True);self.assertEqual(set(a.focus_guid),{'c','o'})
  a.view_action('toggle');self.assertEqual(set(a.focus_guid),{'c'})
