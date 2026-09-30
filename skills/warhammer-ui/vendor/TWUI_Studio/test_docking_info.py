import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from pathlib import Path
from component_options import paired_change,ComponentOptions
from component_info import info_text
from edit_support import History
from model import Document
class DockingTests(unittest.TestCase):
 def test_pair_add_remove_and_history(self):
  for key,value in [('docking','Center Left'),('dock_offset','10,20')]:
   original={'priority':'45'};added=paired_change(original,key,value)
   self.assertIn('docking',added);self.assertIn('dock_offset',added)
   h=History(original);h.record(added)
   for remove in ('docking','dock_offset'):self.assertEqual(paired_change(added,remove,None),original)
   self.assertEqual(h.undo(),original);self.assertEqual(h.redo(),added)
 def test_history_boundary_does_not_render(self):
  ui=SimpleNamespace(history=History({}),render=Mock())
  ComponentOptions.travel(ui);ComponentOptions.travel(ui,True);ui.render.assert_not_called()
 def test_offset_independent_from_docking(self):
  d=Document((Path(__file__).parent/'examples/frame_slaves_expense.twui.xml').read_text(encoding='utf-8-sig'))
  c=next(c for c in d.components if c.get('dock_offset'))
  edited=Document(d.patch([(c,{'offset':'12,34'})]));n=edited.by_guid[c.get('this')]
  self.assertEqual(n.get('dock_offset'),c.get('dock_offset'));self.assertEqual(n.get('offset'),'12,34')
  info=info_text(edited,c.get('this'));self.assertIn('offset = 12,34',info);self.assertIn('dock_offset = '+c.get('dock_offset'),info)
