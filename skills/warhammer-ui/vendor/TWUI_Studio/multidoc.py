from layout_geometry import position_offset_key
from i18n import tr, trf
import copy,uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from model import Document
from workspace import Workspace
from project import save_project,load_project
from component_edit import copied_component,deleted_component,moved_component,subtree

class MultiDocument:
 def setup_multi(self,left,right,compare):
  self.documents=[];self.active_document=-1;self.switching=False;self.component_clipboard=None
  from tab_bar import DocumentTabs
  self.tabs=DocumentTabs(right,self.close_document);self.tabs.pack(fill='x',before=compare);self.tabs.bind('<<NotebookTabChanged>>',self.change_tab);self.tabs.bind('<Button-3>',self.tab_menu)
  from resource_browser import ResourceBrowser
  from vertical_split import VerticalSplit
  resources_split=VerticalSplit(self.left_split);resources_split.fraction=.6;self.left_split.add(resources_split)
  self.mod_resource_root=''
  self.mod_resource_browser=ResourceBrowser(resources_split,self,mod=True);resources_split.add(self.mod_resource_browser)
  self.resource_browser=ResourceBrowser(resources_split,self);resources_split.add(self.resource_browser)
  self.tree.bind('<Control-r>',self.rename_component_dialog)
  self.tree.bind('<Control-R>',self.rename_component_dialog)
  self.bind('<Control-n>',lambda e:self.new_project())
  for widget in (self.canvas,self.tree):
   widget.bind('<Control-c>',lambda e:self.copy_component())
   widget.bind('<Control-v>',lambda e:self.paste_component())
   widget.bind('<Delete>',lambda e:self.delete_component())
  self.cut_pending=None
  self.tree.bind('<Control-x>',self.cut_component)
  self.tree.bind('<Control-X>',self.cut_component)
  self.tree.bind('<Escape>',self.cancel_cut)
  self.new_project(initial=True)
 def rename_component_dialog(self,event=None):
  selected=list(self.tree.selection())
  if len(selected)!=1 or selected[0] not in self.doc.by_guid:return 'break'
  if not self.document_switch_allowed():return 'break'
  guid=selected[0];name=self.doc.by_guid[guid].get('id','')
  win=tk.Toplevel(self);win.title(tr('컴포넌트 이름 바꾸기'));win.geometry('440x130');win.transient(self);win.grab_set()
  value=tk.StringVar(value=name);entry=ttk.Entry(win,textvariable=value);entry.pack(fill='x',padx=12,pady=15);entry.select_range(0,'end');entry.focus_set()
  def apply(event=None):
   try:source=self.doc.rename(guid,value.get().strip())
   except ValueError as error:messagebox.showerror(tr('이름 바꾸기'),str(error),parent=win);return 'break'
   self.selected=guid;self.commit(source,tr('컴포넌트 이름 바꾸기'));self.reveal_tree(guid);win.destroy();return 'break'
  ttk.Button(win,text=tr('적용'),command=apply).pack(side='right',padx=12)
  ttk.Button(win,text=tr('취소'),command=win.destroy).pack(side='right')
  win.bind('<Return>',apply);win.bind('<Escape>',lambda e:win.destroy())
  return 'break'
 def blank_payload(self,name='unknown.twui.xml'):
  g=str(uuid.uuid4()).upper();s=str(uuid.uuid4()).upper()
  xml=f'<layout version="141">\n <hierarchy><root this="{g}"/></hierarchy>\n <components>\n <root this="{g}" uniqueguid="{g}" id="root" currentstate="{s}" defaultstate="{s}">\n <states><newstate this="{s}" uniqueguid="{s}" name="NewState" width="1600" height="900"/></states>\n </root>\n </components>\n</layout>'
  return {'format':'TWUIStudio','version':1,'xml':xml,'original_xml':xml,'source_name':name,'bom':False,'view':{},'loc':{},'preview':{}}
 def capture_document(self):
  if self.active_document<0 or not self.doc:return
  record=self.documents[self.active_document];payload=Workspace.snapshot(self)
  if 'checkpoint_xml' in record['payload']:payload['checkpoint_xml']=record['payload']['checkpoint_xml']
  if record['payload'].get('import_path'):payload['import_path']=record['payload']['import_path']
  payload['view'].update({'query':self.tree_query.get(),'expanded':[g for g in self.doc.by_guid if self.tree.exists(g) and self.tree.item(g,'open')],
   'scroll':[[c.canvasx(0),c.canvasy(0)] for c in (self.canvas,self.original_canvas)]})
  record.update(payload=payload,undo=list(self.undo_stack),redo=list(self.redo_stack),saved_source=self.saved_source,dirty=self.dirty)
 def snapshot(self):
  if not hasattr(self,'documents'):return Workspace.snapshot(self)
  self.capture_document()
  return {'format':'TWUIStudio','version':2,'active':self.active_document,'documents':copy.deepcopy([d['payload'] for d in self.documents])}
 def add_document(self,payload,initial_blank=False):
  self.capture_document();self.documents.append({'payload':payload,'undo':[],'redo':[],'saved_source':payload.get('checkpoint_xml',payload['xml']),'dirty':payload['xml']!=payload.get('checkpoint_xml',payload['xml'])})
  if initial_blank:self.documents[-1].update(pristine_xml=payload['xml'],ever_edited=False)
  self.switching=True;frame=ttk.Frame(self.tabs.notebook);self.tabs.add(frame,text=payload.get('source_name') or 'unknown.twui.xml');self.tabs.select(frame);self.switching=False
  self.activate_document(len(self.documents)-1)
  if 'zoom' not in payload.get('view',{}):
   record=self.documents[-1]
   self.after_idle(lambda:self.fit_view() if self.active_document>=0 and self.documents[self.active_document] is record else None)
 def activate_document(self,index):
  self.cut_pending=None
  self.switching=True;self.active_document=index;record=self.documents[index];p=record['payload'];v=p.get('view',{})
  self.mod_resource_root=p.get('mod_resource_root','')
  if hasattr(self,'mod_resource_browser'):
   self.mod_resource_browser.query.set('');self.mod_resource_browser.reload()
  self.doc=Document(p['xml']);self.original_doc=Document(p['original_xml']);self.file=Path(p.get('source_name') or 'unknown.twui.xml');self.bom=p.get('bom',False)
  self.undo_stack=list(record['undo']);self.redo_stack=list(record['redo']);self.saved_source=record['saved_source'];self.dirty=record['dirty']
  self.zoom=v.get('zoom',1);self.selected=v.get('selected');self.focus_guid=v.get('focus');self.hidden=set(v.get('hidden',[]));self.locks=set(v.get('locks',[]));self.root_lock.set(v.get('root_lock',True));self.hidden_images=set();self.preview=dict(p.get('preview',{}));self.loc=dict(p.get('loc',{}));self.drag=None
  self.tree.delete(*self.tree.get_children());self.tree_query.set(v.get('query',''));self.resource_key=None;self.refresh_resources();self.rebuild()
  expanded=set(v.get('expanded',[]))
  if 'expanded' in v:
   for g in self.doc.by_guid:
    if self.tree.exists(g):self.tree.item(g,open=g in expanded)
  for c,pos in zip((self.canvas,self.original_canvas),v.get('scroll',[])):
   if isinstance(pos,list) and len(pos)==2 and all(isinstance(x,(int,float)) for x in pos):
    r=list(map(float,c.cget('scrollregion').split()));left,top=pos
    if len(r)==4:
     r=[min(r[0],left-32),min(r[1],top-32),max(r[2],left+c.winfo_width()+32),max(r[3],top+c.winfo_height()+32)];c.configure(scrollregion=r);c.xview_moveto((left-r[0])/(r[2]-r[0]));c.yview_moveto((top-r[1])/(r[3]-r[1]))
  self.tabs.select(index);self.switching=False
  if hasattr(self,'refresh_history'):self.refresh_history()
 def change_tab(self,e=None):
  if self.switching or not self.tabs.tabs():return
  index=self.tabs.index(self.tabs.select())
  if index==self.active_document:return
  # Finish or close a properties draft before switching its underlying document.
  from inspector import ComponentInspector
  for w in list(self.winfo_children()):
   if isinstance(w,ComponentInspector):
    self.switching=True;self.tabs.select(self.active_document);self.switching=False
    w.lift();messagebox.showinfo(tr('속성 창'),tr('속성 창을 적용하거나 닫은 뒤 다른 XML로 이동하세요.'),parent=w);return
  self.capture_document();self.activate_document(index)
 def untouched_default(self):
  if len(self.documents)!=1 or getattr(self,'project_path',None) is not None:return False
  record=self.documents[0]
  return ('pristine_xml' in record and not record.get('ever_edited',False)
   and self.doc.source==record['pristine_xml'] and not self.loc and not self.preview)
 def discard_ok(self):
  if self.untouched_default():return True
  edited_default=(len(self.documents)==1 and 'pristine_xml' in self.documents[0]
   and self.documents[0].get('ever_edited',False) and getattr(self,'project_path',None) is None)
  if self.doc and (self.snapshot()!=self.session_saved or edited_default):return messagebox.askyesno(tr('저장하지 않은 프로젝트'),tr('저장하지 않은 프로젝트 변경을 버릴까요?'))
  return True
 def document_switch_allowed(self):
  from inspector import ComponentInspector
  for w in self.winfo_children():
   if isinstance(w,ComponentInspector):
    w.lift();messagebox.showinfo(tr('속성 창'),tr('속성 창을 적용하거나 닫은 뒤 문서를 변경하세요.'),parent=w);return False
  return True
 def new_project(self,initial=False):
  if not initial and not self.document_switch_allowed():return
  if not initial and not self.discard_ok():return
  self.reset_documents();self.project_path=None;self.add_document(self.blank_payload(),initial_blank=True);self.mark_saved()
 def new_xml(self):
  if not self.document_switch_allowed():return
  names={d['payload']['source_name'] for d in self.documents};i=1;name='unknown.twui.xml'
  while name in names:name=f'unknown_{i}.twui.xml';i+=1
  self.add_document(self.blank_payload(name))
 def reset_documents(self):
  self.switching=True
  for tab in self.tabs.tabs():self.tabs.nametowidget(tab).destroy()
  self.documents=[];self.active_document=-1;self.switching=False
 def import_xml(self,path=None):
  if not self.document_switch_allowed():return
  paths=[str(path)] if path else filedialog.askopenfilenames(filetypes=[('TWUI XML','*.xml')])
  loaded=[]
  try:
   for item in paths:
    p=Path(item);raw=p.read_bytes();source=raw.decode('utf-8-sig');Document(source)
    loaded.append({'format':'TWUIStudio','version':1,'xml':source,'original_xml':source,'source_name':p.name,'import_path':str(p),'bom':raw.startswith(b'\xef\xbb\xbf'),'view':{},'loc':{},'preview':{}})
  except Exception as e:messagebox.showerror(tr('가져오기 실패'),str(e));return
  for payload in loaded:
   self.add_document(payload)
   from diagnostics import initial_issues
   if initial_issues(self.doc):
    from diagnostics_ui import show_diagnostics
    show_diagnostics(self,initial=True)
 def save_workspace(self,save_as=False):
  path=self.project_path if not save_as else None
  path=path or filedialog.asksaveasfilename(initialfile='TWUI_project.twuiproj',defaultextension='.twuiproj',filetypes=[(tr('TWUI 프로젝트'),'*.twuiproj')])
  if not path:return
  try:save_project(path,self.snapshot())
  except Exception as e:messagebox.showerror(tr('프로젝트 저장 실패'),str(e));return
  self.project_path=Path(path);self.mark_saved();self.status.set(tr('전체 프로젝트 저장 완료: ')+str(path))
 def open_project(self):
  if not self.document_switch_allowed():return
  path=filedialog.askopenfilename(filetypes=[(tr('TWUI 프로젝트'),'*.twuiproj')])
  if not path or not self.discard_ok():return
  try:data=load_project(path)
  except Exception as e:messagebox.showerror(tr('프로젝트 열기 실패'),str(e));return
  payloads=data['documents'] if data['version']==2 else [data]
  root=payloads[0].get('resource_root','')
  if root and Path(root).is_dir() and not Path(self.settings.get('resource') or '__unset__').is_dir():self.settings['resource']=root
  self.reset_documents()
  for payload in payloads:self.add_document(payload)
  self.capture_document();self.activate_document(data.get('active',0));self.project_path=Path(path);self.resource_browser.reload();self.mark_saved()
 def close_document(self,index=None):
  if not self.document_switch_allowed():return
  self.capture_document();index=self.active_document if index is None else index;record=self.documents[index];p=record['payload']
  if record['dirty']:
   answer=messagebox.askyesnocancel(tr('문서 닫기'),p['source_name']+tr('의 변경 내용을 XML 파일로 저장할까요?'))
   if answer is None:return
   if answer:
    path=filedialog.asksaveasfilename(initialfile=p['source_name'],defaultextension='.xml',filetypes=[('XML','*.xml')])
    if not path:return
    try:
     from project import atomic_write
     atomic_write(path,(b'\xef\xbb\xbf' if p.get('bom') else b'')+p['xml'].encode('utf-8'))
    except OSError as e:messagebox.showerror(tr('저장 실패'),str(e));return
  active=self.active_document;self.switching=True;self.tabs.nametowidget(self.tabs.tabs()[index]).destroy();self.documents.pop(index);self.switching=False;self.active_document=-1
  if self.documents:self.activate_document(min(active-(index<active),len(self.documents)-1))
  else:self.add_document(self.blank_payload(),initial_blank=True)
 def copy_component(self):
  self.cancel_cut()
  if self.selected in self.doc.by_guid:self.component_clipboard=(self.doc.source,self.selected);self.status.set(tr('컴포넌트와 자식 복사됨 · 대상 부모 선택 후 Ctrl+V'))
  return 'break'
 def cut_component(self,event=None):
  from hierarchy_edit import ensure_unique
  if len(self.tree.selection())!=1:return 'break'
  try:ensure_unique(self.doc,self.selected)
  except ValueError as e:messagebox.showinfo(tr('잘라내기'),str(e));return 'break'
  self.cut_pending=(self.doc.source,self.selected);self.tree_states();return 'break'
 def cancel_cut(self,event=None):
  self.cut_pending=None
  if getattr(self,'doc',None):self.tree_states()
  return 'break'
 def detach_component(self):
  from hierarchy_edit import detach
  if self.selected not in self.doc.by_guid:return 'break'
  try:source=detach(self.doc.source,self.selected)
  except ValueError as e:messagebox.showinfo(tr('부모 연결 해제'),str(e));return 'break'
  self.cancel_cut();self.commit(source,tr('부모 연결 해제'));return 'break'
 def paste_component(self):
  from hierarchy_edit import move,detach,NO_PARENT
  pending=getattr(self,'cut_pending',None)
  if pending:
   source,key=pending
   if source!=self.doc.source:
    self.cancel_cut();messagebox.showinfo(tr('잘라내기'),tr('문서가 변경되었습니다. 다시 잘라내기 하세요.'));return 'break'
   try:result=detach(source,key) if self.selected==NO_PARENT else move(source,key,self.selected)
   except ValueError as e:messagebox.showinfo(tr('붙여넣기'),str(e));return 'break'
   self.cut_pending=None;self.selected=key;self.commit(result,tr('계층 이동'));self.tree_states();self.reveal_tree(key);return 'break'
  if not self.component_clipboard or self.selected not in self.doc.by_guid:return 'break'
  try:source,g=copied_component(*self.component_clipboard,self.doc.source,self.selected)
  except ValueError as e:messagebox.showerror(tr('붙여넣기'),str(e));return 'break'
  self.refresh_resources();self.selected=g;self.commit(source);self.reveal_tree(g);return 'break'
 def delete_component(self):
  if self.selected in self.doc.missing_keys:
   from hierarchy_edit import remove_missing
   key=self.selected;source=remove_missing(self.doc,key);self.selected=self.doc.parents.get(key)
   self.commit(source,tr('정의 없는 계층만 삭제'));return 'break'
  if self.selected not in self.doc.by_guid or self.is_locked(self.selected):return 'break'
  try:source=deleted_component(self.doc.source,self.selected)
  except ValueError as e:messagebox.showinfo(tr('삭제'),str(e));return 'break'
  self.selected=self.doc.parents.get(self.selected);self.commit(source);return 'break'
 def move_parent_dialog(self):
  if self.selected not in self.doc.by_guid or self.is_locked(self.selected):return
  g=self.selected;excluded=[n.get('this') for n in self.doc.hierarchy_nodes[g].descendants()];ids=[key for key in self.doc.by_guid if key not in excluded]
  win=tk.Toplevel(self);win.title(tr('부모 변경'));win.geometry('650x140');win.transient(self)
  def path(key):
   names=[]
   while key:names.append(self.doc.by_guid[key].get('id'));key=self.doc.parents.get(key)
   return '/'.join(reversed(names))
  combo=ttk.Combobox(win,state='readonly',values=[path(key) for key in ids]);combo.pack(fill='x',padx=10,pady=12)
  def apply():
   if combo.current()<0:return
   try:
    from hierarchy_edit import move
    source=move(self.doc.source,g,ids[combo.current()])
   except ValueError as e:messagebox.showinfo(tr('부모 변경'),str(e),parent=win);return
   self.commit(source);self.reveal_tree(g);win.destroy()
  ttk.Button(win,text=tr('선택한 부모 아래로 이동'),command=apply).pack();win.grab_set()
 def alt_duplicate(self,x_value,y_value):
  original=self.selected;parent=self.doc.parents.get(original)
  if not parent:return
  try:
   source,g=copied_component(self.doc.source,original,self.doc.source,parent);doc=Document(source);c=doc.by_guid[g]
   parent_node=doc.by_guid[parent]
   if parent_node.child('LayoutEngine') is None:source=doc.patch([(c,{position_offset_key(c):f'{x_value},{y_value}'})])
   self.selected=g;self.commit(source);self.reveal_tree(g)
  except ValueError as e:self.populate();messagebox.showinfo(tr('복사'),str(e))

 def checkpoint_tab(self,index=None):
  if not self.document_switch_allowed():return
  self.capture_document();index=self.active_document if index is None else index;p=self.documents[index]['payload']
  p['checkpoint_xml']=p['xml'];self.documents[index]['saved_source']=p['xml'];self.documents[index]['dirty']=False
  if index==self.active_document:self.saved_source=self.doc.source;self.dirty=False
  self.tabs.tab(index,text=p['source_name']);self.status.set(tr('탭 상태 저장됨 · 파일에 보관하려면 프로젝트 저장 또는 XML 내보내기를 사용하세요.'))
 def can_duplicate_tab(self,index):
  p=self.documents[index]['payload'];return bool(p.get('checkpoint_xml') and p['checkpoint_xml']!=p['original_xml'])
 def duplicate_tab(self,index):
  if not self.document_switch_allowed():return
  self.capture_document()
  if not self.can_duplicate_tab(index):return
  p=copy.deepcopy(self.documents[index]['payload']);name=p['source_name'];suffix='.twui.xml' if name.endswith('.twui.xml') else '.xml';base=name[:-len(suffix)];names={r['payload']['source_name'] for r in self.documents};i=1
  while f'{base}_copy_{i}{suffix}' in names:i+=1
  p['source_name']=f'{base}_copy_{i}{suffix}';p['xml']=p['checkpoint_xml'];p['original_xml']=p['xml'];p.pop('checkpoint_xml',None);self.add_document(p)
 def close_all_tabs(self):
  if not self.document_switch_allowed():return
  if not messagebox.askyesno(tr('탭 전체 닫기'),tr('모든 탭을 닫을까요? 저장하지 않은 내용은 사라집니다. 필요한 프로젝트는 먼저 저장하세요.')):return
  self.reset_documents();self.project_path=None;self.add_document(self.blank_payload(),initial_blank=True)
 def tab_menu(self,e):
  try:index=self.tabs.index('@%d,%d'%(e.x,e.y))
  except tk.TclError:return
  self.capture_document();menu=tk.Menu(self,tearoff=False)
  for label,command in [(tr('탭 닫기'),lambda:self.close_document(index)),(tr('모든 탭 닫기'),self.close_all_tabs),(tr('새 XML 탭'),self.new_xml),(tr('탭 상태 저장'),lambda:self.checkpoint_tab(index))]:menu.add_command(label=label,command=command)
  menu.add_command(label=tr('저장한 상태로 탭 복사'),command=lambda:self.duplicate_tab(index),state='normal' if self.can_duplicate_tab(index) else 'disabled')
  try:menu.tk_popup(e.x_root,e.y_root)
  finally:menu.grab_release()
