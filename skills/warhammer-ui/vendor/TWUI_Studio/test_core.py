import unittest
from pathlib import Path
from model import Document,Resources
from rendering import raster,dimensions
BASE=Path(__file__).resolve().parent
class CoreTests(unittest.TestCase):
 def setUp(self):self.source=(BASE/'examples/frame_slaves_expense.twui.xml').read_bytes().decode('utf-8');self.doc=Document(self.source)
 def test_no_edit_is_byte_identical(self):self.assertEqual(self.doc.patch([]).encode(),self.source.encode())
 def test_patch_changes_only_requested_attribute(self):
  c=next(c for c in self.doc.components if c.get('id')=='slaves_icon');old=c.get('dock_offset');s=self.doc.patch([(c,{'dock_offset':'41.00,0.00'})]);new=Document(s)
  self.assertEqual(new.by_guid[c.get('this')].get('dock_offset'),'41.00,0.00')
  restored=new.patch([(new.by_guid[c.get('this')],{'dock_offset':old})]);self.assertEqual(restored,self.source)
 def test_legacy_comparison_preserved(self):
  self.assertIn('< 0',self.source);c=self.doc.components[-1];new=self.doc.patch([(c,{'offset':'3,4'})]);self.assertIn('< 0',new);Document(new)
 def test_special_text(self):
  t=next(n for n in self.doc.nodes if n.tag=='component_text');s=self.doc.patch([(t,{'text':'<새 값> & "test"'})]);d=Document(s)
  self.assertEqual(next(n for n in d.nodes if n.tag=='component_text').get('text'),'<새 값> & "test"')
 def test_duplicate_ids_different_guids(self):
  s='<layout><hierarchy><root this="a"><same this="b"/><same this="c"/></root></hierarchy><components><root this="a"/><same this="b" id="same"/><same this="c" id="same"/></components></layout>'
  d=Document(s);self.assertEqual(d.children['a'],['b','c']);self.assertEqual(len(d.by_guid),3)
 def test_resource_paths(self):
  r=Resources([str(BASE/'examples')]);self.assertTrue(r.resolve('ui/skins/default/icon_def_slaves_income.png'));self.assertIsNone(r.resolve('../README_KO.md'));self.assertIsNone(r.resolve('ui/missing.png'))
 def test_raster_and_auto_height(self):
  r=Resources([str(BASE/'examples')]);c=next(c for c in self.doc.components if c.get('id')=='frame_slaves_expense');m=self.doc.state(c).child('imagemetrics').children[0]
  im=raster(r.resolve('ui/skins/default/parchment_divider.png'),240,70,m);self.assertEqual(im.size,(240,70));self.assertEqual(im.mode,'RGBA')
  full=dimensions(self.doc,c.get('this'),set(),{})[1];holder=next(c for c in self.doc.components if c.get('id')=='slaves_expense_holder')
  short=dimensions(self.doc,c.get('this'),{holder.get('this')},{})[1];self.assertGreater(full,short)
 def test_invalid_xml_rejected(self):
  with self.assertRaises(Exception):Document('<layout><broken></layout>')
if __name__=='__main__':unittest.main()
