import unittest
from unittest.mock import MagicMock,patch
from multidoc import MultiDocument
from tab_history import TabHistory
from model import Document

class DefaultDocumentTests(unittest.TestCase):
 def setUp(self):
  self.app=MultiDocument();a=self.app;p=a.blank_payload()
  a.doc=Document(p['xml']);a.documents=[{'pristine_xml':p['xml'],'ever_edited':False}]
  a.project_path=None;a.loc={};a.preview={};a.session_saved={}
  a.snapshot=MagicMock(return_value={'view':'changed by initial fit'})

 def test_untouched_default_ignores_initial_view_changes(self):
  with patch('multidoc.messagebox.askyesno') as question:
   self.assertTrue(self.app.discard_ok());question.assert_not_called()

 def test_edit_then_undo_still_requires_confirmation(self):
  a=self.app;a.active_document=0;a.undo_stack=[];a.redo_stack=[];a.refresh_history=lambda:None
  before={'xml':a.doc.source};a.action_state=lambda:{'xml':a.doc.source.replace('1600','1650')}
  TabHistory.record_action(a,before,'edit')
  a.snapshot.return_value=a.session_saved
  with patch('multidoc.messagebox.askyesno',return_value=False) as question:
   self.assertFalse(a.discard_ok());question.assert_called_once()

 def test_imported_blank_does_not_get_default_exemption(self):
  del self.app.documents[0]['pristine_xml']
  with patch('multidoc.messagebox.askyesno',return_value=False) as question:
   self.assertFalse(self.app.discard_ok());question.assert_called_once()

 def test_saved_project_is_not_a_default(self):
  self.app.project_path='existing.twuiproj'
  with patch('multidoc.messagebox.askyesno',return_value=False):self.assertFalse(self.app.discard_ok())

 def test_close_all_creates_fresh_default_after_confirmation(self):
  a=self.app;a.document_switch_allowed=lambda:True
  a.reset_documents=MagicMock();a.add_document=MagicMock();a.project_path='old.twuiproj'
  with patch('multidoc.messagebox.askyesno',return_value=True):a.close_all_tabs()
  a.reset_documents.assert_called_once();self.assertIsNone(a.project_path)
  self.assertTrue(a.add_document.call_args.kwargs['initial_blank'])

 def test_auxiliary_content_is_not_discarded_silently(self):
  self.app.loc={'key':'translation'}
  with patch('multidoc.messagebox.askyesno',return_value=False):self.assertFalse(self.app.discard_ok())
