import unittest,tempfile,zipfile,json
from pathlib import Path
from project import save_project,load_project,export_zip,safe_ui_path
from model import Document,Resources
BASE=Path(__file__).resolve().parent
class WorkspaceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.source=(BASE/'examples/frame_slaves_expense.twui.xml').read_bytes().decode('utf-8')
  self.doc=Document(self.source);self.resources=Resources([BASE/'examples'])
 def payload(self):return {'format':'TWUIStudio','version':1,'xml':self.source,'original_xml':self.source,'view':{'zoom':1.25,'hidden':[],'selected':None},'preview':{},'loc':{}}
 def test_project_keeps_original_after_edit_and_reload(self):
  d=self.payload();c=self.doc.components[-1];d['xml']=self.doc.patch([(c,{'offset':'71,9'})]);d['preview']={c.get('this'):'-20.25'}
  p=self.root/'work.twuiproj';save_project(p,d);loaded=load_project(p)
  self.assertEqual(loaded,d);self.assertNotEqual(loaded['xml'],loaded['original_xml'])
 def test_unknown_version_rejected_without_overwrite(self):
  p=self.root/'work.twuiproj';p.write_text('old');d=self.payload();d['version']=999
  with self.assertRaises(ValueError):save_project(p,d)
  self.assertEqual(p.read_text(),'old')
 def test_export_exact_xml_and_images(self):
  p=self.root/'mod.zip';r=export_zip(p,self.doc,self.resources,'ui/campaign ui/mod/frame.xml',True);self.assertTrue(r['written'])
  with zipfile.ZipFile(p) as z:
   self.assertEqual(z.read('ui/campaign ui/mod/frame.xml'),b'\xef\xbb\xbf'+self.source.encode())
   self.assertIn('ui/skins/default/icon_def_slaves_income.png',z.namelist());self.assertEqual(len(z.namelist()),4)
 def test_missing_resource_does_not_overwrite_export(self):
  p=self.root/'mod.zip';p.write_bytes(b'previous');r=export_zip(p,self.doc,Resources([]),'ui/a.xml')
  self.assertFalse(r['written']);self.assertEqual(len(r['missing']),3);self.assertEqual(p.read_bytes(),b'previous')
 def test_unsafe_export_paths_rejected(self):
  for path in ['../outside.xml','ui/../outside.xml','C:/ui/a.xml','/ui/a.xml','ui/a:stream.xml']:
   with self.assertRaises(ValueError):safe_ui_path(path)
 def test_invalid_project_numbers(self):
  for value in [float('nan'),float('inf'),-1,'1']:
   d=self.payload();d['view']['zoom']=value
   with self.assertRaises(ValueError):save_project(self.root/'bad.twuiproj',d)
 def test_source_crlf_preserved(self):
  d=self.payload();d['xml']=self.source.replace('\n','\r\n');p=self.root/'crlf.twuiproj';save_project(p,d);self.assertEqual(load_project(p)['xml'],d['xml'])
if __name__=='__main__':unittest.main()
