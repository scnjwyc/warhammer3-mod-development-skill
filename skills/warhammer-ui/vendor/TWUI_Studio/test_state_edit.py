import unittest
from pathlib import Path
from model import Document
from state_edit import add_state,add_state_child,state_node,merge_states

class StateEditTests(unittest.TestCase):
 def setUp(self):
  self.source=(Path(__file__).parent/'examples/frame_slaves_expense.twui.xml').read_text(encoding='utf-8-sig');self.doc=Document(self.source)
  self.c=next(c for c in self.doc.components if c.get('id')=='slaves_icon');self.guid=self.c.get('this');self.state=self.doc.state(self.c)
 def test_duplicate_guid_and_image_links(self):
  source,guid=add_state(self.source,self.guid,self.state.get('this'));doc=Document(source);new=state_node(doc,self.guid,guid)
  self.assertNotEqual(guid,self.state.get('this'))
  old_ids={n.get('this') for n in self.state.descendants() if n.get('this')};new_ids={n.get('this') for n in new.descendants() if n.get('this')}
  self.assertFalse(old_ids&new_ids)
  self.assertEqual([n.get('componentimage') for n in self.state.descendants() if n.get('componentimage')],[n.get('componentimage') for n in new.descendants() if n.get('componentimage')])
  self.assertEqual(doc.by_guid[self.guid].get('currentstate'),self.c.get('currentstate'))
 def test_new_state_add_text_metric_and_merge(self):
  source,guid=add_state(self.source,self.guid)
  source=add_state_child(source,self.guid,guid,'text')
  image=self.c.child('componentimages').children[0].get('this')
  source=add_state_child(source,self.guid,guid,'image',image)
  draft=Document(source);state=state_node(draft,self.guid,guid)
  source=draft.patch([(state.child('component_text'),{'text':'새 텍스트 & < >','textlabel':'sample_key'}),(draft.by_guid[self.guid],{'currentstate':guid})])
  target=self.doc.patch([(self.c,{'tooltiplabel':'separate_edit'})]);merged=Document(merge_states(target,source,self.guid));c=merged.by_guid[self.guid]
  self.assertEqual(c.get('tooltiplabel'),'separate_edit');self.assertEqual(c.get('currentstate'),guid)
  state=merged.state(c);self.assertEqual(state.child('component_text').get('text'),'새 텍스트 & < >');self.assertEqual(state.child('imagemetrics').children[0].get('componentimage'),image)
 def test_reject_invalid_image_link(self):
  with self.assertRaises(ValueError):add_state_child(self.source,self.guid,self.state.get('this'),'image','invalid')
 def test_merge_untouched_states_preserves_document(self):
  self.assertEqual(merge_states(self.source,self.source,self.guid),self.source)
