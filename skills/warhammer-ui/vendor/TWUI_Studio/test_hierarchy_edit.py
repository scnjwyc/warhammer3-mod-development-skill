import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
from model import Document
from hierarchy_edit import move,detach,remove_missing,NO_PARENT
from diagnostics import marker_kind
from app import Studio
from multidoc import MultiDocument

SOURCE='<layout><hierarchy><root this="r"><a this="a"><b this="b"/></a><c this="c"/><missing this="m"/></root></hierarchy><components><root this="r" id="root"/><a this="a"/><b this="b"/><c this="c"/><unused this="u"/></components></layout>'
class HierarchyTests(unittest.TestCase):
 def test_move_preserves_definitions_guids_children(self):
  d=Document(move(SOURCE,'a','c'))
  self.assertEqual(d.children['c'],['a']);self.assertEqual(d.children['a'],['b'])
  self.assertEqual(d.source.split('<components>')[1],SOURCE.split('<components>')[1])
 def test_detach_and_attach_unused(self):
  d=Document(detach(SOURCE,'a'));self.assertTrue({'a','b','u'}<=d.unlinked_keys)
  r=Document(move(d.source,'a','c'));self.assertEqual(r.children['c'],['a']);self.assertIn('b',r.unlinked_keys)
 def test_unused_can_be_parent(self):
  d=Document(move(SOURCE,'a','u'));self.assertEqual(d.children['u'],['a']);self.assertEqual(d.children['a'],['b']);self.assertNotIn('u',d.unlinked_keys)
 def test_cycle_and_self_rejected(self):
  for parent in ('a','b'):
   with self.assertRaises(ValueError):move(SOURCE,'a',parent)
 def test_missing_delete_only_hierarchy(self):
  d=Document(SOURCE);self.assertIn('m',d.missing_keys)
  self.assertEqual(marker_kind(d.issues_by_key['m']),'missing')
  result=remove_missing(d,'m');self.assertEqual(result,SOURCE.replace('<missing this="m"/>',''))
 def test_missing_wrapper_keeps_valid_children(self):
  s=SOURCE.replace('<missing this="m"/>','<missing this="m"><unused this="u"/></missing>')
  d=Document(remove_missing(Document(s),'m'));self.assertEqual(d.parents['u'],'r');self.assertFalse(d.missing_keys)
 def test_real_definition_cannot_use_missing_delete(self):
  with self.assertRaises(ValueError):remove_missing(Document(SOURCE),'a')
 def test_tree_selection_does_not_parse_or_redraw_scenes(self):
  app=SimpleNamespace(tree=MagicMock(),selected=None,populate=MagicMock(),refresh_selection=MagicMock(),draw=MagicMock())
  app.tree.selection.return_value=('m',)
  with patch('app.Document',side_effect=AssertionError('selection must not parse')):
   Studio.select_tree(app)
  app.draw.assert_not_called();app.refresh_selection.assert_called_once();self.assertEqual(app.selected,'m')
 def test_delete_missing_ignores_placeholder_edit_lock(self):
  d=Document(SOURCE);app=SimpleNamespace(doc=d,selected='m',is_locked=lambda k:True,commit=MagicMock())
  MultiDocument.delete_component(app)
  self.assertEqual(app.commit.call_args.args[0],SOURCE.replace('<missing this="m"/>',''))
 def test_cut_paste_moves_atomically_and_clears_pending(self):
  app=SimpleNamespace(doc=Document(SOURCE),selected='c',cut_pending=(SOURCE,'a'),commit=MagicMock(),tree_states=MagicMock(),reveal_tree=MagicMock())
  MultiDocument.paste_component(app)
  result=Document(app.commit.call_args.args[0]);self.assertEqual(result.parents['a'],'c');self.assertIsNone(app.cut_pending)
 def test_cut_to_no_parent(self):
  app=SimpleNamespace(doc=Document(SOURCE),selected=NO_PARENT,cut_pending=(SOURCE,'a'),commit=MagicMock(),tree_states=MagicMock(),reveal_tree=MagicMock())
  MultiDocument.paste_component(app)
  self.assertIn('a',Document(app.commit.call_args.args[0]).unlinked_keys)
 def test_no_parent_tree_group_is_last_and_unused_inside(self):
  doc=Document(SOURCE);tree=MagicMock();tree.selection.return_value=[];tree.exists.return_value=False;tree.get_children.return_value=[]
  query=MagicMock();query.get.return_value=''
  app=SimpleNamespace(doc=doc,tree=tree,selected=None,focus_guid=None,tree_query=query,xml_viewer=MagicMock(),diagnostic_icons={},populate=MagicMock(),tree_states=MagicMock(),draw=MagicMock())
  with patch('diagnostics_ui.install_tree_warnings'):
   Studio.rebuild(app)
  calls=tree.insert.call_args_list
  groups=[c.kwargs['iid'] for c in calls if c.args[0]=='']
  self.assertEqual(groups[-1],NO_PARENT)
  self.assertEqual(next(c.args[0] for c in calls if c.kwargs['iid']=='u'),NO_PARENT)
 def test_original_cut_source_changes_cancel_move(self):
  app=SimpleNamespace(doc=Document(SOURCE+' '),selected='c',cut_pending=(SOURCE,'a'),cancel_cut=MagicMock(),commit=MagicMock())
  with patch('multidoc.messagebox.showinfo'):
   MultiDocument.paste_component(app)
  app.commit.assert_not_called();app.cancel_cut.assert_called_once()
 def test_ambiguous_definition_not_missing(self):
  d=Document('<layout><hierarchy><a this="x"/></hierarchy><components><a this="x"/><a this="x"/></components></layout>')
  self.assertNotIn('x',d.missing_keys)

if __name__=='__main__':unittest.main()
