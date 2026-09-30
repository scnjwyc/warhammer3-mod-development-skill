import unittest
from pathlib import Path
from model import Document
from edit_support import History
class ComponentEditing(unittest.TestCase):
 def setUp(self):
  self.doc=Document((Path(__file__).parent/'examples/frame_slaves_expense.twui.xml').read_text(encoding='utf-8-sig'))
 def test_rename_keeps_guid_links(self):
  for c in self.doc.components:
   if c.get('id')=='header_slaves_expense':break
  guid=c.get('this');new=Document(self.doc.rename(guid,'aaaa'))
  self.assertEqual(new.by_guid[guid].tag,'aaaa');self.assertEqual(new.by_guid[guid].get('id'),'aaaa')
  self.assertEqual(next(n for n in new.hierarchy.descendants() if n.get('this')==guid).tag,'aaaa')
  self.assertIn('</aaaa>',new.source)
  self.assertEqual(set(self.doc.by_guid),set(new.by_guid))
 def test_invalid_id_rejected(self):
  with self.assertRaises(ValueError):self.doc.rename(self.doc.components[0].get('this'),'a b')
 def test_remove_option_preserves_other_content(self):
  c=self.doc.components[1];key='priority';self.assertIn(key,c.attrs)
  result=Document(self.doc.patch([(c,{key:None})]));attrs=dict(c.attrs);attrs.pop(key)
  self.assertEqual(result.by_guid[c.get('this')].attrs,attrs)
 def test_deleted_option_undo_redo(self):
  history=History({'allowhorizontalresize':'false'});history.record({})
  self.assertEqual(history.undo(),{'allowhorizontalresize':'false'});self.assertEqual(history.redo(),{})
