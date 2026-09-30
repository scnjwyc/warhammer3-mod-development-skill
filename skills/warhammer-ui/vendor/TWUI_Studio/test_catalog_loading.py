import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from component_options import load_catalog

class CatalogLoadingTests(unittest.TestCase):
 def test_korean_windows_default_encoding(self):
  # Emulate Path.read_text's Windows default while preserving explicit encoding.
  original=Path.read_text
  def windows_read(path,encoding=None,errors=None):
   return original(path,encoding=encoding or 'cp949',errors=errors)
  path=Path(__file__).parent/'component_options.json'
  with patch.object(Path,'read_text',windows_read):
   with self.assertRaises(UnicodeDecodeError):path.read_text()
   catalog,error=load_catalog(path)
  self.assertIsNone(error)
  self.assertIn('allowhorizontalresize',catalog)
  self.assertEqual(catalog,json.loads(original(path,encoding='utf-8')))
 def test_missing_corrupt_and_malformed_catalog_fallback(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'options.json'
   for content in (None,b'\xff',b'{',b'[]',b'{"docking":[]}'):
    if content is not None:path.write_bytes(content)
    catalog,error=load_catalog(path)
    self.assertEqual(catalog,{})
    self.assertTrue(error)

class InspectorApplyTests(unittest.TestCase):
 def test_id_apply_updates_xml_and_closes_inspector(self):
  from types import SimpleNamespace
  from unittest.mock import Mock
  from inspector import ComponentInspector
  from model import Document,pair
  doc=Document((Path(__file__).parent/'examples/frame_slaves_expense.twui.xml').read_text(encoding='utf-8-sig'))
  c=next(c for c in doc.components if c.get('id')=='header_slaves_expense')
  state=doc.state(c);position_key='dock_offset' if c.get('docking') else 'offset'
  x,y=pair(c.get(position_key,c.get('offset','0,0')))
  app=SimpleNamespace(doc=doc,is_locked=lambda g:False)
  def commit(source,label=None):app.doc=Document(source);app.label=label
  app.commit=commit
  dimensions={k:SimpleNamespace(get=lambda v=v:str(v)) for k,v in {'x':x,'y':y,'width':state.get('width','0'),'height':state.get('height','0')}.items()}
  inspector=SimpleNamespace(app=app,guid=c.get('this'),baseline=doc.source,c=c,inputs=[],dimensions=dimensions,position_key=position_key,options=SimpleNamespace(changes=lambda:{}),id_value=SimpleNamespace(get=lambda:'aaaa'),destroy=Mock())
  inspector.original_baseline=doc.source
  inspector.collect_source=lambda:ComponentInspector.collect_source(inspector)
  ComponentInspector.apply(inspector)
  self.assertEqual(app.doc.by_guid[c.get('this')].get('id'),'aaaa')
  self.assertEqual(app.doc.by_guid[c.get('this')].tag,'aaaa')
  self.assertEqual(next(n for n in app.doc.hierarchy.descendants() if n.get('this')==c.get('this')).tag,'aaaa')
  inspector.destroy.assert_called_once()
  self.assertEqual(app.label,'속성 적용')
