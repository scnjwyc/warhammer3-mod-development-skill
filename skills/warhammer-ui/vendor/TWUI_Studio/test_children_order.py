import unittest
from pathlib import Path
from unittest.mock import MagicMock
from types import SimpleNamespace
from model import Document
from component_edit import reordered_children
from inspector import ComponentInspector

class ChildrenOrderTests(unittest.TestCase):
 def test_reverse_preserves_subtrees_definitions_and_restores_exactly(self):
  source=(Path(__file__).parent/'examples/frame_slaves_expense.twui.xml').read_text()
  doc=Document(source);parent=next(c.get('this') for c in doc.components if c.get('id')=='frame_slaves_expense')
  order=doc.children[parent];changed=reordered_children(source,parent,list(reversed(order)));new=Document(changed)
  self.assertEqual(new.children[parent],list(reversed(order)))
  self.assertEqual(source[source.index('<components>'):],changed[changed.index('<components>'):])
  for g in order:self.assertEqual(doc.children[g],new.children[g])
  self.assertEqual(reordered_children(changed,parent,order),source)
  self.assertEqual(reordered_children(source,parent,order),source)
  with self.assertRaises(ValueError):reordered_children(source,parent,order[:-1])
 def test_short_content_scroll_region_covers_viewport(self):
  owner=SimpleNamespace(canvas=MagicMock(),content=MagicMock())
  owner.canvas.winfo_height.return_value=500;owner.canvas.winfo_width.return_value=600;owner.content.winfo_reqheight.return_value=90
  ComponentInspector.update_scroll_bounds(owner)
  owner.canvas.configure.assert_called_with(scrollregion=(0,0,600,500));owner.canvas.yview_moveto.assert_called_with(0)
  owner.canvas.reset_mock();owner.content.winfo_reqheight.return_value=900
  ComponentInspector.update_scroll_bounds(owner)
  owner.canvas.configure.assert_called_with(scrollregion=(0,0,600,900));owner.canvas.yview_moveto.assert_not_called()
