import unittest
from unittest.mock import MagicMock
from model import Document
from tab_history import TabHistory
from usability import Usability
from vertical_split import bounded_fraction
from multidoc import MultiDocument
class App(TabHistory,Usability):
 def draw(self):pass
 def tree_states(self):pass
 def rebuild(self):pass
class HistoryTests(unittest.TestCase):
 def setUp(self):
  self.a=App();a=self.a;a.doc=Document(MultiDocument.blank_payload(None)['xml']);a.locks=set();a.hidden=set();a.focus_guid=None;a.selected=a.doc.components[0].get('this');a.root_lock=MagicMock();a.root_lock.get.return_value=False;a.undo_stack=[];a.redo_stack=[];a.saved_source=a.doc.source
 def test_xml_then_lock_undo_redo_in_order(self):
  a=self.a;original=a.doc.source;before=a.action_state();a.doc=Document(original.replace('1600','1920'));a.record_action(before);a.lock_action('lock')
  a.history_travel();self.assertFalse(a.locks);self.assertIn('1920',a.doc.source)
  a.history_travel();self.assertEqual(a.doc.source,original)
  a.history_travel(True);self.assertIn('1920',a.doc.source);self.assertFalse(a.locks)
  a.history_travel(True);self.assertIn(a.selected,a.locks)
 def test_focus_and_hidden_restore(self):
  a=self.a;before=a.action_state();a.focus_guid=a.selected;a.hidden.add(a.selected);a.record_action(before);a.history_travel();self.assertIsNone(a.focus_guid);self.assertFalse(a.hidden);a.history_travel(True);self.assertEqual(a.focus_guid,a.selected)
 def test_noop_lock_and_exhausted_history(self):
  a=self.a;a.lock_action('lock');a.lock_action('lock');self.assertEqual(len(a.undo_stack),1);a.history_travel();a.history_travel();self.assertEqual(len(a.redo_stack),1)
 def test_new_action_discards_redo(self):
  a=self.a;a.lock_action('lock');a.history_travel();before=a.action_state();a.hidden.add(a.selected);a.record_action(before);self.assertFalse(a.redo_stack)
 def test_quarter_bounds(self):
  self.assertEqual(bounded_fraction(.1),.25);self.assertEqual(bounded_fraction(.9),.75);self.assertEqual(bounded_fraction(.6),.6)
