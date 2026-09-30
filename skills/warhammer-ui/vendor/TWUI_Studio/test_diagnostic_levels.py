import unittest
from model import Document
from diagnostics import initial_issues, highest_severity
from component_edit import reordered_children

class DiagnosticLevelTests(unittest.TestCase):
 def doc(self,h,c):return Document('<layout><hierarchy>'+h+'</hierarchy><components>'+c+'</components></layout>')
 def test_case_difference_is_yellow_not_initial(self):
  d=self.doc('<bl_parent this="g"/>','<bl_parent this="g" id="BL_parent"/>')
  self.assertEqual(highest_severity(d.issues),'warning');self.assertFalse(initial_issues(d))
 def test_reference_difference_with_matching_names_is_red(self):
  d=self.doc('<bl_parent this="bl_parent"/>','<bl_parent this="BL_parent" id="bl_parent"/>')
  self.assertEqual(d.by_guid['bl_parent'].get('id'),'bl_parent')
  self.assertEqual(highest_severity(d.issues),'error');self.assertTrue(initial_issues(d))
 def test_unused_is_grey_and_does_not_block_other_order(self):
  d=self.doc('<root this="r"><a this="a"/><b this="b"/></root>','<root this="r"/><a this="a"/><b this="b"/><unused this="u" id="unused"/>')
  self.assertEqual(highest_severity(d.issues_by_key['u']),'info');self.assertFalse(initial_issues(d))
  self.assertEqual(Document(reordered_children(d.source,'r',['b','a'])).children['r'],['b','a'])
  renamed=Document(d.rename('u','new_unused'))
  self.assertEqual(renamed.by_guid['u'].tag,'new_unused')
 def test_missing_hierarchy_target_stays_red(self):
  d=self.doc('<absent this="x"/>','<other this="y"/>')
  self.assertTrue(initial_issues(d));self.assertEqual(highest_severity(d.issues_by_key['x']),'error')
 def test_real_name_disagreement_stays_red(self):
  d=self.doc('<a this="a"/>','<b this="a" id="b"/>')
  self.assertTrue(initial_issues(d))
 def test_id_only_difference_is_yellow_in_both_views(self):
  d=self.doc('<filters_holder this="g"/>','<filters_holder this="g" id="sort_holder"/>')
  self.assertFalse(initial_issues(d))
  self.assertEqual(highest_severity(d.issues_by_key['g']),'warning')
  self.assertTrue(all(highest_severity(v)=='warning' for v in d.issues_by_line.values()))
 def test_this_uniqueguid_difference_is_red(self):
  d=self.doc('<a this="g"/>','<a this="g" uniqueguid="different" id="a"/>')
  self.assertTrue(initial_issues(d));self.assertEqual(highest_severity(d.issues),'error')
 def test_id_warning_cannot_mask_guid_error(self):
  d=self.doc('<a this="g"/>','<a this="other" id="b"/>')
  self.assertEqual(highest_severity(d.issues_by_key['g']),'error')

 def test_parentheses_ids_are_preserved_and_not_duplicate_names(self):
  d=self.doc('<root this="r"><tx_ this="a"/><tx_ this="b"/></root>','<root this="r"/><tx_ this="a" id="tx_("/><tx_ this="b" id="tx_)"/>')
  self.assertFalse(d.issues)
  self.assertEqual(d.rename('a','tx_('),d.source)
  renamed=Document(d.rename('a','label_(left)'))
  self.assertEqual(renamed.by_guid['a'].get('id'),'label_(left)')
  self.assertEqual(renamed.by_guid['a'].tag,'label_left')
  self.assertFalse(renamed.issues)
 def test_strongest_marker_wins(self):
  d=self.doc('<a this="g"/><a this="g"/>','<a this="g" id="A"/>')
  self.assertEqual(highest_severity(d.issues_by_key['g']),'error')

if __name__=='__main__':unittest.main()
