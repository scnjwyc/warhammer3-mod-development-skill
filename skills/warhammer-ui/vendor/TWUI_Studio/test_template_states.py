import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from model import Document
from template_states import TemplateIndex,state_items,merge_template_texts,template_index
XML='''<layout><hierarchy><button this="instance"/></hierarchy><components><button this="instance" uniqueguid="instance" id="button" template_id="button" part_of_template="true" uniqueguid_in_template="base"><state_uniqueguids><state_uniqueguid name="active" uniqueguid="local"/></state_uniqueguids><localised_texts><localised_text/><localised_text state="active" text="old" text_label="label"/></localised_texts></button></components></layout>'''
TEMPLATE='''<layout><hierarchy><button this="base"/></hierarchy><components><button this="base" id="button"><states><active this="original" name="active" width="30" height="30"><component_text font_m_size="12"/></active></states></button></components></layout>'''
class TemplateTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);(self.root/'templates').mkdir();self.path=self.root/'templates/button.twui.xml';self.path.write_text(TEMPLATE)
 def test_guid_and_state_resolve_from_original_ui_root(self):
  index=TemplateIndex(str(self.root));path,c=index.resolve(Document(XML),'instance')
  self.assertEqual(path,self.path);self.assertEqual(c.find('./states/active').get('this'),'original')
  items,mode=state_items(Document(XML).by_guid['instance']);self.assertTrue(mode);self.assertEqual(items[0].get('uniqueguid'),'local')
 def test_cache_refresh_and_path_change(self):
  a=SimpleNamespace(settings={'resource':str(self.root)});index=template_index(a);index.load();self.path.unlink()
  self.assertIsNotNone(index.resolve(Document(XML),'instance'));self.assertIs(template_index(a),index)
  a.template_index=None;self.assertIsNone(template_index(a).resolve(Document(XML),'instance'))
  a.settings['resource']='';self.assertIsNone(template_index(a).root)
 def test_missing_and_corrupt_templates_do_not_break_local_states(self):
  self.path.write_text('broken');index=TemplateIndex(str(self.root));self.assertIsNone(index.resolve(Document(XML),'instance'));self.assertEqual(len(index.errors),1)
  self.assertIsNone(TemplateIndex('').resolve(Document(XML),'instance'))
 def test_only_edited_text_attributes_merge(self):
  draft=XML.replace('text="old"','text="new &amp; text"');target=XML.replace('id="button"','id="changed"').replace('text_label="label"','text_label="other"')
  merged=merge_template_texts(target,draft,XML,'instance');c=Document(merged).by_guid['instance']
  self.assertEqual(c.get('id'),'changed');self.assertEqual(c.child('localised_texts').children[1].get('text_label'),'other')
  self.assertIn('text="new &amp; text"',merged);self.assertIn('uniqueguid="local"',merged);self.assertEqual(self.path.read_text(),TEMPLATE)
 def test_direct_states_unaffected(self):
  items,mode=state_items(Document(TEMPLATE).by_guid['base']);self.assertFalse(mode);self.assertEqual(items[0].get('this'),'original')
 def test_ambiguous_templates_not_guessed(self):
  (self.root/'templates/other.twui.xml').write_text(TEMPLATE.replace('width="30"','width="50"'))
  xml=XML.replace('template_id="button"','')
  self.assertIsNone(TemplateIndex(str(self.root)).resolve(Document(xml),'instance'))
 def test_template_editor_text_apply_and_disabled_actions(self):
  import tkinter as tk
  from states_editor import StatesEditor
  try:root=tk.Tk()
  except tk.TclError as error:self.skipTest(str(error))
  try:
   owner=SimpleNamespace(guid='instance',baseline=XML,app=SimpleNamespace(settings={'resource':str(self.root)}))
   editor=StatesEditor(root,owner);root.update()
   self.assertEqual(editor.state_ids,['local']);self.assertTrue(all(str(b.cget('state'))=='disabled' for b in editor.state_buttons))
   editor.groups[0][1].change('text','edited');result=editor.apply_to(XML)
   self.assertIn('text="edited"',result);self.assertNotIn('<states>',result);self.assertEqual(self.path.read_text(),TEMPLATE)
   editor.add(False);self.assertEqual(editor.state_ids,['local'])
  finally:root.destroy()
 def test_real_inspector_navigation_and_apply(self):
  import tkinter as tk
  from app import Studio
  from inspector import ComponentInspector
  try:probe=tk.Tk();probe.destroy()
  except tk.TclError as error:self.skipTest(str(error))
  app=Studio();errors=[];app.report_callback_exception=lambda *a:errors.append(a)
  try:
   app.settings['resource']=str(self.root)
   payload=app.blank_payload();payload.update(xml=XML,original_xml=XML)
   app.add_document(payload);app.selected='instance';app.update()
   from unittest.mock import patch
   with patch.object(TemplateIndex,'load',side_effect=AssertionError('Template read during zoom')) as load:
    app.fit_view();app.set_zoom(app.zoom/1.15);app.set_zoom(app.zoom*1.15);app.update();load.assert_not_called()
   original_resolve=TemplateIndex.resolve
   with patch.object(TemplateIndex,'resolve',autospec=True,side_effect=original_resolve) as resolve:
    win=ComponentInspector(app);app.update();self.assertGreater(resolve.call_count,0)
    calls=resolve.call_count
    win.nav.selection_set('states');app.update();win.nav.selection_set('component');app.update()
    win.nav.selection_set('states');app.update();self.assertEqual(resolve.call_count,calls)
   win.nav.selection_set('state:0');app.update()
   self.assertEqual(win.page,'states')
   self.assertEqual(list(win.nav_state_guids.values()),['local'])
   editor=win.states_editor;editor.groups[0][1].change('text','inspector edit')
   result=win.collect_source();self.assertIn('text="inspector edit"',result)
   app.commit(result);app.undo();self.assertEqual(app.doc.source,XML)
   app.redo();self.assertEqual(app.doc.source,result)
   win.destroy()
  finally:
   for job in app.tk.call('after','info'):app.tk.call('after','cancel',job)
   app.destroy()
  self.assertEqual(errors,[])
