import unittest
from pathlib import Path
from model import Document
from edit_support import History,expression_display,expression_value
BASE=Path(__file__).parent
class EditingTests(unittest.TestCase):
 def test_first_deletion_undo_redo(self):
  h=History('ContextTextLabel');h.record('ContextTextLabe')
  self.assertEqual(h.undo(),'ContextTextLabel');self.assertEqual(h.redo(),'ContextTextLabe')
  h.undo();h.record('New');self.assertEqual(h.redo(),'New')
 def test_tooltip_inserted_above_guid_preserving_indent(self):
  for nl in ('\n','\r\n'):
   src=(BASE/'examples/frame_slaves_expense.twui.xml').read_text().replace('\n',nl);d=Document(src)
   n=next(c for c in d.components if c.get('id')=='dy_slaves')
   out=d.patch([(n,{'tooltiplabel':'aaaa'})]);new=Document(out);node=new.by_guid[n.get('this')]
   token=out[node.start:node.end]
   self.assertIn(nl+'\t\t\ttooltiplabel="aaaa"'+nl+'\t\t\tuniqueguid=',token)
   self.assertEqual(node.get('tooltiplabel'),'aaaa')
 def test_expression_noop_preserves_original(self):
  src=(BASE/'examples/frame_slaves_expense.twui.xml').read_text();d=Document(src)
  n=next(n for n in d.nodes if n.get('context_function_id') and 'settlement_slave_expense_total' in n.get('context_function_id'))
  raw=n.get('context_function_id');visible=expression_display(raw)
  self.assertFalse(visible.startswith(('\n',' ')))
  self.assertEqual(expression_value(raw,visible,src,n),raw)
 def test_expression_changed_lines_survive(self):
  src=(BASE/'examples/frame_slaves_expense.twui.xml').read_text();d=Document(src)
  n=next(n for n in d.nodes if n.get('context_function_id'))
  edited='Sum(Value)\n  * 2\n< 0';value=expression_value(n.get('context_function_id'),edited,src,n)
  self.assertEqual(expression_display(value),edited)
  out=d.patch([(n,{'context_function_id':value})]);Document(out)
  self.assertIn('&lt; 0',out)
if __name__=='__main__':unittest.main()
