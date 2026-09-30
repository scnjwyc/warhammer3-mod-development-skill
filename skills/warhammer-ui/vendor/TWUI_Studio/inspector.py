from i18n import tr, trf
from inspector_navigation import InspectorNavigation
from user_properties import UserProperties,apply_user_properties
from states_editor import StatesEditor
from image_rows import build_images
from layout_edit import apply_layout_settings,format_layout
from layout_options import LayoutOptions
from types import SimpleNamespace
from transform import fixed2
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
import json,math
from model import Document,pair
from component_options import ComponentOptions
from confirmed_choice import ConfirmedChoice
from inspector_scroll import install_scrolling
from edit_support import bind_entry_history,expression_display,expression_value

def resource_relative(path,roots):
 p=Path(path).resolve()
 for root in roots:
  root=Path(root).resolve()
  try:rel=p.relative_to(root).as_posix()
  except ValueError:continue
  if rel.startswith('ui/'):return rel
  if root.name.lower()=='ui':return 'ui/'+rel
  if root.name.lower()=='default':return 'ui/skins/default/'+rel
 return None

def suggestions(query,values):
 query=query.casefold()
 return sorted((v for v in values if query in v.casefold()),key=lambda v:(not v.casefold().startswith(query),v))[:30]

class ComponentInspector(InspectorNavigation,tk.Toplevel):
 def __init__(self,app):
  super().__init__(app);self.app=app;self.guid=app.selected;self.baseline=app.doc.source;self.c=app.doc.by_guid[self.guid];self.inputs=[]
  self.title(self.c.get('id','')+tr(' · 속성'));self.transient(app);self.minsize(720,400)
  bx,by,bw,bh=app.boxes.get(self.guid,(0,0,100,100));z=app.zoom
  x=app.canvas.winfo_rootx()+int(32+(bx+bw)*z-app.canvas.canvasx(0))+12;y=app.canvas.winfo_rooty()+int(32+by*z-app.canvas.canvasy(0))
  self.geometry(f'820x650+{max(0,min(x,self.winfo_screenwidth()-840))}+{max(0,min(y,self.winfo_screenheight()-690))}')
  self.original_baseline=self.baseline;self.draft_history=[];self.draft_future=[]
  self.build()
 def update_scroll_bounds(self):
  # A region shorter than the viewport allows Tk to expose empty space.
  height=max(self.canvas.winfo_height(),self.content.winfo_reqheight())
  self.canvas.configure(scrollregion=(0,0,max(1,self.canvas.winfo_width()),height))
  if self.content.winfo_reqheight()<=self.canvas.winfo_height():self.canvas.yview_moveto(0)
 def build(self):
  app=self.app;self.extra_groups=[]
  try:catalog=json.loads((Path(__file__).parent/'cco_catalog.json').read_text(encoding='utf-8-sig'))
  except (OSError,ValueError):catalog={'callbacks':[],'contexts':[]}
  ttk.Label(self,text=tr('적용하면 XML에 반영됩니다. 후보는 참고자료에서 관찰된 값입니다.'),padding=8).pack(fill='x')
  bottom=ttk.Frame(self,padding=8);bottom.pack(side='bottom',fill='x');ttk.Button(bottom,text=tr('적용'),command=self.apply).pack(side='right');ttk.Button(bottom,text=tr('닫기'),command=self.destroy).pack(side='right',padx=6)
  main=ttk.Frame(self,padding=6);main.pack(fill='both',expand=True);self.make_navigation(main)
  area=ttk.Frame(main);area.pack(fill='both',expand=True);self.canvas=tk.Canvas(area,highlightthickness=0);self.canvas.pack(side='left',fill='both',expand=True)
  sb=ttk.Scrollbar(area,orient='vertical',command=self.canvas.yview);sb.pack(side='right',fill='y');self.canvas.configure(yscrollcommand=sb.set)
  self.content=ttk.Frame(self.canvas,padding=8);window=self.canvas.create_window(0,0,window=self.content,anchor='nw')
  self.canvas.bind('<Configure>',lambda e:(self.canvas.itemconfigure(window,width=e.width),self.update_scroll_bounds()));self.content.bind('<Configure>',lambda e:self.update_scroll_bounds())
  body=self.section('component')
  ttk.Label(body,text=tr('컴포넌트 ID')).pack(anchor='w')
  self.id_value=tk.StringVar(value=self.c.get('id',''));id_entry=ttk.Entry(body,textvariable=self.id_value);id_entry.pack(fill='x',pady=(2,6));bind_entry_history(id_entry,self.id_value)
  self.position_key='offset'
  xy=pair(self.c.get(self.position_key,self.c.get('offset','0,0')));state=app.doc.state(self.c);self.dimensions={}
  for title,keys,values in [(tr('위치 (')+self.position_key+')',('x','y'),xy)]:
   row=ttk.Frame(body);row.pack(fill='x',pady=4);ttk.Label(row,text=title,width=17).pack(side='left')
   for key,value in zip(keys,values):
    ttk.Label(row,text={'x':'X','y':'Y','width':tr('너비'),'height':tr('높이')}[key]).pack(side='left',padx=(6,3));v=tk.StringVar(value=fixed2(value));entry=ttk.Entry(row,textvariable=v,width=10);entry.pack(side='left');bind_entry_history(entry,v);self.dimensions[key]=v
  self.options=ComponentOptions(body,self.c,allow_custom=True)
  self.field(body,self.c,'tooltiplabel',tr('툴팁 라벨'))
  body=self.section('callbacks');self.section_buttons(body,'callbackwithcontextlist')
  callbacks=self.c.child('callbackwithcontextlist')
  if callbacks and callbacks.children:
   for i,node in enumerate(callbacks.children):
    frame=ttk.LabelFrame(body,text=trf('콜백 {0}', i + 1),padding=8);frame.pack(fill='x',pady=5)
    self.anchor('callbacks',trf('콜백 {0}', i + 1),frame)
    ttk.Button(frame,text=tr('콜백 삭제'),command=lambda index=i:self.structural('callbackwithcontextlist','remove',index)).pack(anchor='e')
    self.field(frame,node,'callback_id','callback_id',options=catalog['callbacks'],complete=True)
    self.field(frame,node,'context_object_id',tr('CCO 객체'),options=catalog['contexts'],complete=True)
    ttk.Label(frame,text='context_function_id').pack(anchor='w')
    editor=ttk.Frame(frame);editor.pack(fill='x',expand=True);editor.columnconfigure(0,weight=1);editor.columnconfigure(1,minsize=16)
    text=tk.Text(editor,height=5,wrap='word',undo=True,font=('Consolas',10),highlightthickness=2,highlightbackground='#a0a0a0',highlightcolor='#2585db',relief='flat')
    text.grid(row=0,column=0,sticky='nsew')
    textbar=ttk.Scrollbar(editor,orient='vertical',command=text.yview);textbar._wheel_target=text
    def scroll_changed(first,last,bar=textbar):
     bar.set(first,last)
     if float(first)>0.00001 or float(last)<0.99999:
      if not bar.winfo_manager():bar.grid(row=0,column=1,sticky='ns')
     elif bar.winfo_manager():bar.grid_remove()
    text.configure(yscrollcommand=scroll_changed)
    text.insert('1.0',expression_display(node.get('context_function_id','')));text.edit_reset()
    text.bind('<FocusIn>',lambda e,t=text:t.configure(highlightbackground='#2585db'))
    text.bind('<FocusOut>',lambda e,t=text:t.configure(highlightbackground='#a0a0a0'))
    def grow(e=None,t=text):
     # Include wrapped display lines, retain scrolling for exceptionally long expressions.
     if not t.winfo_exists():return
     lines=int(t.index('end-1c').split('.')[0]);display=t.count('1.0','end','displaylines');lines=max(lines,display[0] if display else 1)
     height=max(5,min(20,lines+1))
     if int(t.cget('height'))!=height:t.configure(height=height)
    text.bind('<KeyRelease>',grow);text.bind('<Configure>',grow);self.after_idle(grow)
    def text_history(redo=False,t=text,g=grow):
     if not t.tk.getboolean(t.tk.call(t._w,'edit','canredo' if redo else 'canundo')):return 'break'
     try:t.edit_redo() if redo else t.edit_undo()
     except tk.TclError:pass
     g();return 'break'
    def remember_text(e=None,f=text_history):self.last_history=f
    text.bind('<KeyRelease>',remember_text,add='+')
    text.bind('<<Paste>>',remember_text,add='+');text.bind('<<Cut>>',remember_text,add='+')
    text.bind('<Control-z>',lambda e,f=text_history:f())
    text.bind('<Control-Shift-Z>',lambda e,f=text_history:f(True))
    text.bind('<Control-y>',lambda e,f=text_history:f(True))
    extra=ComponentOptions(frame,node,title=tr('추가 콜백 옵션'),reserved={'callback_id','context_object_id','context_function_id','this','uniqueguid'},pair_docking=False,catalog={},allow_custom=True);self.extra_groups.append((node,extra))
    self.inputs.append((node,'context_function_id',lambda t=text,n=node:expression_value(n.get('context_function_id',''),t.get('1.0','end-1c'),self.baseline,n)))
  else:ttk.Label(body,text=tr('이 요소에는 기존 callback_with_context가 없습니다.'),padding=8).pack(anchor='w')
  body=self.section('properties')
  self.user_properties=UserProperties(body,self.c)
  ttk.Button(body,text=tr('유저 프로퍼티 전체 삭제'),command=lambda:self.user_properties.clear()).pack(anchor='e')
  body=self.section('images');self.section_buttons(body,'componentimages')
  ttk.Label(body,text=tr('이미지 삭제 시 모든 스테이트의 연결된 이미지 메트릭도 삭제됩니다.'),wraplength=540).pack(fill='x')
  images=self.c.child('componentimages')
  if images:build_images(self,body,images)
  body=self.section('states')
  self.states_editor=StatesEditor(body,self)
  self.refresh_state_navigation()
  body=self.section('layout')
  layout=self.c.child('LayoutEngine')
  self.layout_options=LayoutOptions(body,layout if layout is not None else SimpleNamespace(attrs={}))
  ttk.Button(body,text=tr('레이아웃 엔진 삭제'),command=lambda:self.layout_options.clear()).pack(anchor='e')
  for seq in ('<Control-z>','<Control-y>','<Control-Shift-Z>'):
   self.bind(seq,lambda e,r=seq!='<Control-z>':getattr(self,'last_history',lambda redo:'break')(r))
  self.make_children_order()
  from radial_preview import RadialPreview
  self.radial_preview=RadialPreview(self.pages['layout'],self)
  self.nav.selection_set('component');self.show_page('component');install_scrolling(self)
 def field(self,parent,node,key,label,options=None,complete=False,browse=False):
  ttk.Label(parent,text=label).pack(anchor='w');row=ttk.Frame(parent);row.pack(fill='x',pady=(2,6));v=tk.StringVar(value=node.get(key,''))
  if complete:
   choice=ConfirmedChoice(self,parent,row,node.get(key,''),options);self.inputs.append((node,key,choice.get));return
  entry=ttk.Entry(row,textvariable=v)
  entry.pack(side='left',fill='x',expand=True);self.inputs.append((node,key,v.get));bind_entry_history(entry,v)
  if browse:
   def choose():
    p=filedialog.askopenfilename(parent=self,filetypes=[(tr('이미지'),'*.png *.jpg *.dds'),(tr('모든 파일'),'*.*')])
    if not p:return
    rel=resource_relative(p,self.app.resources.roots)
    if rel:v.set(rel)
    else:messagebox.showinfo(tr('리소스 경로'),tr('설정된 추출 리소스 폴더 내부의 이미지를 선택하세요. 필요한 이미지를 ui/ 경로에 복사한 뒤 선택할 수 있습니다.'),parent=self)
   ttk.Button(row,text='...',width=3,command=choose).pack(side='right',padx=(5,0))
 def collect_source(self):
  changes={}
  for node,key,get in self.inputs:
   value=get()
   if value!=node.get(key,''):changes.setdefault(node,{})[key]=value
  for node,editor in getattr(self,'extra_groups',[]):
   updates=editor.changes()
   if updates:changes.setdefault(node,{}).update(updates)
  nums={k:float(fixed2(v.get())) for k,v in self.dimensions.items()}
  if not all(math.isfinite(v) for v in nums.values()):raise ValueError(tr('좌표는 유한한 숫자, 크기는 0 이상이어야 합니다.'))
  attrs=changes.setdefault(self.c,{})
  attrs.update(self.options.changes())
  old=pair(self.c.get(self.position_key,self.c.get('offset','0,0')))
  if f"{fixed2(nums['x'])},{fixed2(nums['y'])}"!=self.c.get(self.position_key,''):attrs[self.position_key]=f"{fixed2(nums['x'])},{fixed2(nums['y'])}"
  source=Document(self.baseline).patch(list(changes.items()))
  if hasattr(self,'states_editor'):source=self.states_editor.apply_to(source)
  if hasattr(self,'layout_options') and self.layout_options.values!=self.layout_options.initial:source=apply_layout_settings(source,self.guid,self.layout_options.values)
  if hasattr(self,'user_properties'):source=apply_user_properties(source,self.guid,self.user_properties.values)
  source=format_layout(source,self.guid)
  source=Document(source).rename(self.guid,self.id_value.get().strip())
  return source

 def apply(self):
  if getattr(self,'active_choice',None):self.active_choice.cancel()
  app=self.app
  if app.doc.source!=self.original_baseline or self.guid not in app.doc.by_guid:
   messagebox.showinfo(tr('다시 열기'),tr('문서가 변경됐습니다. 속성 창을 다시 열어주세요.'),parent=self);return
  if app.is_locked(self.guid):messagebox.showinfo(tr('잠금'),tr('잠금을 해제한 뒤 수정하세요.'),parent=self);return
  try:source=self.collect_source()
  except (ValueError,TypeError) as error:
   messagebox.showerror(tr('속성 확인'),str(error),parent=self);return
  app.commit(source,label=tr('속성 적용'))
  if app.doc.source==source:self.destroy()

 def destroy(self):
  app=self.app
  if hasattr(app,'hidden_images'):
   old=app.hidden_images
   app.hidden_images={key for key in old if key[0]!=self.guid}
   if app.hidden_images!=old:app.draw()
  super().destroy()
