import unittest
from model import Document
from diagnostics import repair_hierarchy_guids, repair_duplicate_guids
from component_edit import deleted_component

class DiagnosticsTests(unittest.TestCase):
 def doc(self,h,c):return Document('<layout><hierarchy>'+h+'</hierarchy><components>'+c+'</components></layout>')
 def test_duplicate_reference_is_visible_and_source_unchanged(self):
  d=self.doc('<root this="r"><a this="a"/><a this="a"/><tx_filter this="t"/></root>', '<root this="r"/><a this="a" id="a"/><tx_filter this="t" id="tx_header"/>')
  self.assertEqual(len(d.by_guid),4);self.assertEqual(len(set(d.children['r'])),3)
  self.assertEqual(d.patch([]),d.source)
  self.assertEqual(d.by_guid['t'].tag,'tx_filter')
  self.assertIn('name_mismatch',[i.code for i in d.issues_by_key['t']])
  self.assertTrue(d.issues_by_line)
  self.assertNotIn('@hierarchy',d.source)
 def test_mismatch_and_duplicate_definitions_resolve_by_unused_name(self):
  d=self.doc('<root this="r"><other this="o"><bottom this="valid"/></other><top this="dup"/><bottom this="correct"/></root>', '<root this="r"/><other this="o"/><bottom this="valid"/><bottom this="dup" uniqueguid="dup"/><top this="dup"/>')
  self.assertEqual(d.by_guid['correct'].tag,'bottom')
  self.assertEqual(len(d.guid_repairs),1)
  fixed=Document(repair_hierarchy_guids(d))
  self.assertEqual(fixed.by_guid['correct'].get('uniqueguid'),'correct')
  self.assertFalse(fixed.issues)
 def test_ambiguous_name_does_not_offer_guid_repair(self):
  d=self.doc('<root this="r"><a this="missing"/></root>', '<root this="r"/><a this="one"/><a this="two"/>')
  self.assertFalse(d.guid_repairs);self.assertEqual(len(d.by_guid),4)
  self.assertEqual(d.by_guid['missing'].get('id'),'a')
  self.assertIn('unresolved',[i.code for i in d.issues])
 def test_dangling_parent_does_not_hide_child(self):
  d=self.doc('<missing this="x"><child this="c"/></missing>', '<child this="c"/>')
  self.assertEqual(d.children['x'],['c']);self.assertIn('c',d.by_guid)
 def test_duplicate_definition_is_not_lost(self):
  d=self.doc('<root this="r"><a this="d"/><b this="d"/></root>','<root this="r"/><a this="d"/><b this="d"/>')
  self.assertEqual(len(d.by_guid),3)
  self.assertEqual({d.by_guid[k].tag for k in d.children['r']},{'a','b'})
  self.assertTrue(d.unsafe_keys)
 def test_leaf_split_remaps_local_links_not_text(self):
  d=self.doc('<root this="r"><p this="p"><a this="a"/></p><q this="q"><a this="a"/></q></root>', '<root this="r"/><p this="p"/><q this="q"/><a this="a" uniqueguid="a" currentstate="s"><componentimages><im this="i"/></componentimages><states><s this="s" uniqueguid="s"><image componentimage="i"/><component_text text="a"/></s></states></a>')
  fixed=Document(repair_duplicate_guids(d))
  self.assertFalse(fixed.issues)
  new=fixed.by_guid[fixed.children['q'][0]]
  self.assertNotEqual(new.get('this'),'a')
  self.assertEqual(new.get('this'),new.get('uniqueguid'))
  state=fixed.state(new);image=new.child('componentimages').children[0]
  self.assertEqual(state.child('image').get('componentimage'),image.get('this'))
  self.assertEqual(state.child('component_text').get('text'),'a')
  self.assertEqual(repair_duplicate_guids(fixed),fixed.source)
 def test_non_leaf_alias_not_automatically_cloned(self):
  d=self.doc('<root this="r"><a this="a"><b this="b"/></a><a this="a"/></root>', '<root this="r"/><a this="a"/><b this="b"/>')
  self.assertFalse(d.duplicate_repairs)
  with self.assertRaises(ValueError):deleted_component(d.source,'a')
 def test_normal_repeated_names_in_separate_parents_are_valid(self):
  d=self.doc('<root this="r"><p this="p"><a this="a"/></p><q this="q"><a this="b"/></q></root>', '<root this="r"/><p this="p"/><q this="q"/><a this="a"/><a this="b"/>')
  self.assertFalse(d.issues)
 def test_crlf_repair_only_changes_attributes(self):
  s='<layout>\r\n<hierarchy><a this="h"/></hierarchy>\r\n<components><a this="c" uniqueguid="c"/></components>\r\n</layout>'
  d=Document(s);self.assertEqual(repair_hierarchy_guids(d),s.replace('this="c" uniqueguid="c"','this="h" uniqueguid="h"'))

if __name__=='__main__':unittest.main()
