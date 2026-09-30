import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import MagicMock,patch
from model import Document
from view_state import ViewActions,top_targets,shown
from tab_history import TabHistory
from usability import Usability
from app import Studio

XML='''<layout><hierarchy><root this="r"><parent this="p"><child this="c"/></parent><other this="o"/></root></hierarchy><components>
<root this="r" id="root"><states><s width="500" height="400"/></states><LayoutEngine type="List"/></root>
<parent this="p" id="parent"><states><s width="100" height="80"/></states></parent>
<child this="c" id="child" offset="12,15"><states><s width="20" height="10"/></states></child>
<other this="o" id="other"><states><s width="40" height="30"/></states></other>
</components></layout>'''
class App(ViewActions,TabHistory,Usability):
 def draw(self):pass
 def rebuild(self):pass
 def tree_states(self):pass

class ViewTests(unittest.TestCase):
 def setUp(self):
  a=self.a=App();a.doc=Document(XML);a.saved_source=XML;a.tree=MagicMock();a.tree.selection.return_value=('p','c');a.selected='p';a.hidden={'c'};a.locks=set();a.focus_guid=None;a.root_lock=MagicMock();a.root_lock.get.return_value=False;a.undo_stack=[];a.redo_stack=[]
 def test_ancestor_replaces_selected_descendant(self):
  a=self.a;self.assertEqual(top_targets(a.doc,['c','p','o']),['p','o'])
  a.view_action('toggle');self.assertEqual(a.hidden,{'p','c'});a.view_action('toggle');self.assertEqual(a.hidden,{'c'})
 def test_mixed_roots_and_undo_are_atomic(self):
  a=self.a;a.tree.selection.return_value=('p','o');a.hidden={'o'};a.view_action('toggle');self.assertEqual(a.hidden,{'p','o'});self.assertEqual(len(a.undo_stack),1)
  a.history_travel();self.assertEqual(a.hidden,{'o'});a.history_travel(True);self.assertEqual(a.hidden,{'p','o'});self.assertEqual(a.doc.source,XML)
 def test_only_exact_nodes_ignores_hidden_ancestor(self):
  a=self.a;a.hidden={'r','c'};a.tree.selection.return_value=('c','o');a.view_action('only')
  self.assertEqual({g for g in a.doc.by_guid if shown(a.doc,g,a.hidden,a.focus_guid)},{'c','o'})
  a.view_action('toggle');self.assertFalse(shown(a.doc,'c',a.hidden,a.focus_guid));self.assertIn('r',a.hidden)
  a.view_action('toggle');self.assertTrue(shown(a.doc,'c',a.hidden,a.focus_guid));self.assertFalse(shown(a.doc,'r',a.hidden,a.focus_guid))
 def test_only_subtree_then_narrow_and_undo(self):
  a=self.a;a.hidden={'r','p','c','o'};a.tree.selection.return_value=('p',)
  a.view_action('only');self.assertEqual(set(a.focus_guid),{'p','c'});self.assertEqual(a.hidden,{'r','o'})
  self.assertTrue(shown(a.doc,'c',a.hidden,a.focus_guid))
  a.tree.selection.return_value=('c',);a.view_action('only');self.assertEqual(a.focus_guid,['c'])
  self.assertFalse(shown(a.doc,'p',a.hidden,a.focus_guid))
  a.history_travel();self.assertEqual(set(a.focus_guid),{'p','c'})
  a.history_travel(True);self.assertEqual(a.focus_guid,['c']);self.assertEqual(a.doc.source,XML)
 def test_only_multiple_subtrees_and_noop(self):
  a=self.a;a.tree.selection.return_value=('p','c','o');a.view_action('only')
  self.assertEqual(set(a.focus_guid),{'p','c','o'});self.assertEqual(len(a.undo_stack),1)
  a.view_action('only');self.assertEqual(len(a.undo_stack),1)
 def test_exact_excludes_parent_children_and_restores_history(self):
  a=self.a;a.tree.selection.return_value=('p',);a.hidden={'r','p','c'}
  a.view_action('exact')
  self.assertEqual({g for g in a.doc.by_guid if shown(a.doc,g,a.hidden,a.focus_guid)},{'p'})
  a.history_travel();self.assertIsNone(a.focus_guid);self.assertEqual(a.hidden,{'r','p','c'})
  a.history_travel(True);self.assertEqual(a.focus_guid,['p']);self.assertEqual(a.doc.source,XML)
  a.view_action('all_show');self.assertIsNone(a.focus_guid);self.assertFalse(a.hidden)
 def test_exact_keeps_all_explicit_selections(self):
  a=self.a;a.tree.selection.return_value=('p','c');a.view_action('exact')
  self.assertEqual(set(a.focus_guid),{'p','c'})
 def test_bulk_lock_undo(self):
  a=self.a;a.lock_action('lock');self.assertEqual(a.locks,{'p','c'});self.assertEqual(len(a.undo_stack),1);a.history_travel();self.assertFalse(a.locks)
 def test_child_actions_leave_parent_flag(self):
  a=self.a;a.tree.selection.return_value=('p',);a.hidden=set();a.view_action('children_hide');self.assertEqual(a.hidden,{'c'});a.view_action('children_show');self.assertFalse(a.hidden)
 def test_no_selection_only_noop(self):
  a=self.a;a.tree.selection.return_value=();a.selected=None;a.view_action('only');self.assertFalse(a.undo_stack)
 def test_context_preserves_selection_disables_properties(self):
  a=self.a;a.tree.identify_row.return_value='c'
  for name in ('populate','refresh_selection','open_inspector','cut_component','detach_component','copy_component','paste_component','delete_component','move_parent_dialog'):setattr(a,name,MagicMock())
  with patch('usability.tk.Menu') as Menu:
   a.lock_menu(SimpleNamespace(widget=a.tree,y=1,x_root=1,y_root=1))
   a.tree.selection_set.assert_not_called()
   calls=Menu.return_value.add_command.call_args_list
   self.assertTrue(any(c.kwargs.get('label')=='속성' and c.kwargs.get('state')=='disabled' for c in calls))
 def test_geometry_and_viewport_unchanged_by_visibility(self):
  a=self.a;a.selected=None;a.canvas=MagicMock();a.original_canvas=object();a.zoom=1;a.file=Path('test.xml');a.dirty=False;a.status=MagicMock();a.paint_grid=MagicMock()
  a.canvas.canvasx.return_value=75;a.canvas.canvasy.return_value=55;a.canvas.cget.return_value='0 0 2000 1200';a.canvas.winfo_width.return_value=700;a.canvas.winfo_height.return_value=500;a.canvas.find_all.return_value=[]
  a.hidden=set();Studio.draw_scene(a);original=dict(a.boxes);x=a.canvas.xview_moveto.call_args;y=a.canvas.yview_moveto.call_args
  a.hidden={'p'};Studio.draw_scene(a);self.assertEqual(a.boxes['o'],original['o'])
  a.hidden={'r'};a.focus_guid=['c'];Studio.draw_scene(a);self.assertEqual(a.boxes,{'c':original['c']});self.assertEqual(a.canvas.xview_moveto.call_args,x);self.assertEqual(a.canvas.yview_moveto.call_args,y)

class NoParentViewTests(unittest.TestCase):
 # Reuse the app fixture without inheriting/rerunning the regular view tests.
 def setUp(self):
  ViewTests.setUp(self)
  from hierarchy_edit import NO_PARENT
  a=self.a
  source=XML.replace('</components>','<unused this="u" id="unused"/><unused2 this="v" id="unused2"/></components>')
  a.doc=Document(source);a.saved_source=source;a.selected=NO_PARENT;a.tree.selection.return_value=(NO_PARENT,)
 def test_group_hide_and_isolate_are_atomic_and_leave_xml_unchanged(self):
  a=self.a;source=a.doc.source
  a.view_action('toggle');self.assertEqual(a.hidden,{'c','u','v'})
  a.history_travel();self.assertEqual(a.hidden,{'c'})
  a.history_travel(True);self.assertEqual(a.hidden,{'c','u','v'})
  a.view_action('only');self.assertEqual(set(a.focus_guid),{'u','v'})
  self.assertEqual({g for g in a.doc.by_guid if shown(a.doc,g,a.hidden,a.focus_guid)},{'u','v'})
  self.assertEqual(a.doc.source,source)
 def test_group_child_commands_cover_members(self):
  a=self.a;a.view_action('children_hide');self.assertEqual(a.hidden,{'c','u','v'})
  a.view_action('children_show');self.assertEqual(a.hidden,{'c'})
  a.lock_action('children');self.assertEqual(a.locks,{'u','v'})
 def test_group_lock_unlock_and_undo(self):
  a=self.a;a.lock_action('lock');self.assertEqual(a.locks,{'u','v'})
  self.assertEqual(len(a.undo_stack),1);a.history_travel();self.assertFalse(a.locks)
  a.history_travel(True);a.lock_action('unlock');self.assertFalse(a.locks)
 def test_mixed_selection_keeps_regular_subtree_semantics(self):
  from hierarchy_edit import NO_PARENT
  a=self.a;a.tree.selection.return_value=(NO_PARENT,'p','u')
  a.view_action('only');self.assertEqual(set(a.focus_guid),{'u','v','p','c'})
  self.assertEqual(a.selected_guids(),['p','u'])
 def test_empty_group_cannot_target_old_selection(self):
  a=self.a;a.doc=Document(XML);a.selected='p'
  for action in ('toggle','only','exact','children_hide'):a.view_action(action)
  for action in ('lock','others','children','toggle'):a.lock_action(action)
  self.assertFalse(a.undo_stack);self.assertEqual(a.hidden,{'c'});self.assertFalse(a.locks)
