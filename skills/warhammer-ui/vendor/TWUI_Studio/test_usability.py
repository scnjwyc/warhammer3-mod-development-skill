import unittest
from types import SimpleNamespace
from model import Document
from usability import visibility,Usability
class UsabilityTests(unittest.TestCase):
 def setUp(self):
  self.doc=Document('<layout><hierarchy><root this="r"><parent this="p"><child this="c"/></parent></root></hierarchy><components><root this="r" id="root"/><parent this="p"/><child this="c"/></components></layout>')
 def test_visibility_inherits_without_losing_own_setting(self):
  self.assertEqual(visibility(self.doc,'c',{'p'}),'부모 숨김')
  self.assertEqual(visibility(self.doc,'c',{'p','c'}),'숨김')
  self.assertEqual(visibility(self.doc,'c',set()),'표시')
 def test_parent_lock_does_not_lock_child(self):
  app=SimpleNamespace(doc=self.doc,locks={'p'},root_lock=SimpleNamespace(get=lambda:True))
  self.assertTrue(Usability.is_locked(app,'r'));self.assertTrue(Usability.is_locked(app,'p'));self.assertFalse(Usability.is_locked(app,'c'))
if __name__=='__main__':unittest.main()
