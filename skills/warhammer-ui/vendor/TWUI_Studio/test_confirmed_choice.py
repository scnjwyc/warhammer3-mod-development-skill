import unittest
from confirmed_choice import ConfirmedHistory
class ConfirmedTests(unittest.TestCase):
 def test_user_sequence_cancel_undo_preview(self):
  h=ConfirmedHistory('ContextTextLabel');h.edit('Context');h.edit('ContextAdoptOnCondition');h.confirm()
  self.assertEqual(h.preview(-1),'ContextTextLabel')
  self.assertEqual(h.committed,'ContextAdoptOnCondition')
  self.assertEqual(h.cancel(),'ContextAdoptOnCondition')
 def test_enter_accepts_undo_then_redo_is_preview(self):
  h=ConfirmedHistory('A');h.edit('B');h.confirm();h.preview(-1);h.confirm()
  self.assertEqual(h.committed,'A');self.assertEqual(h.preview(1),'B')
  self.assertEqual(h.committed,'A');h.cancel();self.assertEqual(h.committed,'A')
  h.preview(1);h.confirm();self.assertEqual(h.committed,'B')
 def test_unconfirmed_typing_is_not_in_history(self):
  h=ConfirmedHistory('A');h.edit('partial');h.cancel()
  self.assertEqual(h.values,['A']);self.assertEqual(h.draft,'A')
 def test_new_confirm_after_undo_replaces_future(self):
  h=ConfirmedHistory('A');h.edit('B');h.confirm();h.preview(-1);h.confirm();h.edit('C');h.confirm()
  self.assertEqual(h.values,['A','C'])
if __name__=='__main__':unittest.main()

class DraftHistoryTests(unittest.TestCase):
 def test_partial_undo_redo_without_confirm(self):
  full='CcoCampaignFactionProvinceManager';partial='CcoCampaignFactionProvi'
  h=ConfirmedHistory(full);h.edit(partial)
  self.assertTrue(h.can_preview(-1));self.assertEqual(h.preview(-1),full)
  self.assertTrue(h.can_preview(1));self.assertEqual(h.preview(1),partial)
  self.assertFalse(h.can_preview(1));self.assertEqual(h.committed,full)
 def test_previous_commits_and_draft(self):
  h=ConfirmedHistory('A');h.edit('B');h.confirm();h.edit('partial')
  self.assertEqual(h.preview(-1),'B');self.assertEqual(h.preview(-1),'A')
  self.assertFalse(h.can_preview(-1));self.assertEqual(h.preview(1),'B');self.assertEqual(h.preview(1),'partial')
  h.cancel();self.assertEqual(h.draft,'B');self.assertFalse(h.can_preview(1))
 def test_arrow_second_click_cancels(self):
  from types import SimpleNamespace
  from unittest.mock import Mock
  from confirmed_choice import ConfirmedChoice
  choice=SimpleNamespace(active=lambda:True,list_area=SimpleNamespace(winfo_manager=lambda:'pack'),escape=Mock(return_value='break'))
  self.assertEqual(ConfirmedChoice.show_all(choice),'break');choice.escape.assert_called_once()
