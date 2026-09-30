from i18n import tr, trf
import tkinter as tk
from tkinter import ttk,messagebox
from model import Document
from inspector_structure import edit_section

SECTIONS=[('component',tr('컴포넌트')),('callbacks',tr('콜백')),('properties',tr('유저 프로퍼티')),('images',tr('이미지')),('states',tr('스테이트')),('layout',tr('레이아웃 엔진'))]
class InspectorNavigation:
 def make_navigation(self,parent):
  self.pages={};self.anchors={};self.page_positions={};self.page=None
  navarea=ttk.Frame(parent,width=180);navarea.pack(side='left',fill='y',padx=(0,6));navarea.pack_propagate(False)
  self.nav=ttk.Treeview(navarea,show='tree',selectmode='browse');self.nav.pack(side='left',fill='both',expand=True)
  bar=ttk.Scrollbar(navarea,command=self.nav.yview);bar.pack(side='right',fill='y');self.nav.configure(yscrollcommand=bar.set);self.nav._wheel_target=self.nav
  self.nav.bind('<<TreeviewSelect>>',self.navigate)
  for key,label in SECTIONS:self.nav.insert('','end',iid=key,text=label,open=True)
 def section(self,key):
  page=ttk.Frame(self.content);self.pages[key]=page;return page
 def anchor(self,key,label,widget):
  iid=key+':'+str(len(self.anchors));self.anchors[iid]=(key,widget);self.nav.insert(key,'end',iid=iid,text=label);return iid
 def show_page(self,key,widget=None):
  if getattr(self,'active_choice',None):self.active_choice.cancel()
  if self.page:self.page_positions[self.page]=self.canvas.yview()[0]
  for page in self.pages.values():page.pack_forget()
  self.pages[key].pack(fill='x',expand=True);self.page=key
  if key=='states' and hasattr(self,'states_editor'):self.states_editor.sync_images()
  self.update_idletasks();self.update_scroll_bounds()
  self.canvas.yview_moveto(self.page_positions.get(key,0))
  if widget is not None:
   self.update_idletasks();height=max(1,self.content.winfo_height());y=widget.winfo_rooty()-self.content.winfo_rooty();self.canvas.yview_moveto(max(0,y)/height)
 def navigate(self,e=None):
  selected=self.nav.selection()
  if not selected:return
  iid=selected[0]
  if iid in self.pages:self.show_page(iid)
  elif iid.startswith('state:'):
   editor=self.states_editor
   if not editor.checked_flush():return
   editor.selected=self.nav_state_guids.get(iid); editor.render();self.show_page('states')
  elif iid in self.anchors:self.show_page(*self.anchors[iid])
 def refresh_state_navigation(self):
  if not hasattr(self,'states_editor'):return
  for iid in self.nav.get_children('states'):self.nav.delete(iid)
  editor=self.states_editor;doc=Document(editor.source)
  from template_states import state_items
  items,inherited=state_items(doc.by_guid[self.guid])
  self.nav_state_guids={}
  if items:
   for i,s in enumerate(items):
    key='state:'+str(i);self.nav_state_guids[key]=s.get('uniqueguid') if inherited else s.get('this')
    self.nav.insert('states','end',iid=key,text=s.get('name',s.tag))
 def structural(self,tag,action,index=None):
  if getattr(self,'active_choice',None):self.active_choice.cancel()
  try:
   before=self.collect_source();after=edit_section(before,self.guid,tag,action,index)
  except (ValueError,TypeError) as e:messagebox.showerror(tr('속성 확인'),str(e),parent=self);return
  if before==after:return
  self.draft_history.append(before);self.draft_future.clear();self.rebuild_draft(after,self.page)
 def rebuild_draft(self,source,page):
  self.update_idletasks()
  for w in self.winfo_children():w.destroy()
  self.baseline=source;self.c=Document(source).by_guid[self.guid];self.inputs=[];self.active_choice=None;self.last_history=lambda redo=False:'break'
  self.children_buttons=lambda:None;self.radial_preview=None
  self.build();self.show_page(page or 'component');self.nav.selection_set(page or 'component');self.last_history=self.draft_travel
 def draft_travel(self,redo=False):
  stack=self.draft_future if redo else self.draft_history
  if not stack:return 'break'
  try:current=self.collect_source()
  except (ValueError,TypeError):return 'break'
  (self.draft_history if redo else self.draft_future).append(current);source=stack.pop();self.rebuild_draft(source,self.page);return 'break'
 def make_children_order(self):
  from component_edit import reordered_children
  page=ttk.LabelFrame(self.pages['layout'],text=tr('자식 순서'),padding=6);page.pack(fill='x');doc=Document(self.baseline)
  self.children_order_frame=page
  order=list(doc.children.get(self.guid,[]))
  ttk.Label(page,text=tr('1차 자식 순서 · 적용하면 하이어라키에 반영됩니다.')).pack(anchor='w',pady=6)
  row=ttk.Frame(page);row.pack(fill='x')
  listing=tk.Listbox(row,exportselection=False,height=min(12,max(3,len(order))));listing.pack(side='left',fill='x',expand=True)
  bar=ttk.Scrollbar(row,command=listing.yview);bar.pack(side='right',fill='y');listing.configure(yscrollcommand=bar.set)
  for g in order:listing.insert('end',doc.by_guid[g].get('id',g) if g in doc.by_guid else g)
  buttons=ttk.Frame(page);buttons.pack(fill='x',pady=6)
  def move(delta):
   selection=listing.curselection()
   if not selection:return
   index=selection[0];target=index+delta
   if not 0<=target<len(order):return
   changed=order[:];changed[index],changed[target]=changed[target],changed[index]
   try:
    before=self.collect_source();after=reordered_children(before,self.guid,changed)
   except (ValueError,TypeError) as error:messagebox.showerror(tr('속성 확인'),str(error),parent=self);return
   self.draft_history.append(before);self.draft_future.clear();self.rebuild_draft(after,'layout')
   self.children_list.selection_set(target);self.children_list.see(target);self.children_buttons()
  up=ttk.Button(buttons,text='↑',command=lambda:move(-1));up.pack(side='left')
  down=ttk.Button(buttons,text='↓',command=lambda:move(1));down.pack(side='left',padx=4)
  def states(event=None):
   selection=listing.curselection();index=selection[0] if selection else -1
   enabled=True
   listing.configure(state='normal' if enabled else 'disabled')
   up.configure(state='normal' if enabled and index>0 else 'disabled')
   down.configure(state='normal' if enabled and 0<=index<len(order)-1 else 'disabled')
  listing.bind('<<ListboxSelect>>',states);states();self.children_list=listing;self.children_buttons=states

 def section_buttons(self,parent,tag):
  row=ttk.Frame(parent);row.pack(fill='x',pady=5)
  ttk.Button(row,text=tr('추가 +'),command=lambda:self.structural(tag,'add')).pack(side='left')
  label=tr('전체 삭제 (연결된 메트릭 포함)') if tag=='componentimages' else tr('전체 삭제')
  ttk.Button(row,text=label,command=lambda:self.structural(tag,'remove')).pack(side='right')
