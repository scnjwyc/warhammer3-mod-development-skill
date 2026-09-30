from i18n import tr, trf
import json,math
from pathlib import Path
import tkinter as tk
from tkinter import ttk,messagebox
from model import Document
from template_states import state_items,template_index,merge_template_texts
import xml.etree.ElementTree as ET
from component_options import ComponentOptions
from state_edit import state_node,add_state,add_state_child,merge_states,remove_state,remove_state_child
from transform import fixed2

class StatesEditor(ttk.LabelFrame):
 def __init__(self,parent,owner):
  super().__init__(parent,text=tr('states · 상태'),padding=6);self.pack(fill='x',pady=6)
  self.owner=owner;self.guid=owner.guid;self.source=owner.baseline;self.initial=self.source;self.groups=[];self.history=[];self.future=[]
  self.catalog=json.loads((Path(__file__).parent/'state_catalog.json').read_text(encoding='utf-8-sig'))
  doc=Document(self.source);current=doc.state(doc.by_guid[self.guid]);self.selected=current.get('this') if current else None
  self.top=ttk.Frame(self);self.top.pack(fill='x');self.choice=ttk.Combobox(self.top,state='readonly');self.choice.pack(fill='x');self.choice.bind('<<ComboboxSelected>>',self.select)
  buttons=ttk.Frame(self);buttons.pack(fill='x');self.state_buttons=[]
  for label,command in [(tr('상태 추가'),lambda:self.add(False)),(tr('상태 복제'),lambda:self.add(True)),(tr('상태 삭제'),self.remove),(tr('현재 상태로 사용'),lambda:self.use('currentstate')),(tr('기본 상태로 사용'),lambda:self.use('defaultstate'))]:
   button=ttk.Button(buttons,text=label,command=command);button.pack(side='left');self.state_buttons.append(button)
  self.status=ttk.Label(self);self.status.pack(fill='x')
  self.body=ttk.Frame(self);self.body.pack(fill='x');self.render()
 def flush(self):
  doc=Document(self.source);changes=[]
  for node,editor in self.groups:
   updates=editor.changes()
   for key in ('width','height'):
    if key in updates and updates[key] is not None:
     value=fixed2(updates[key])
     if float(value)<0:raise ValueError(tr('너비와 높이는 0 이상이어야 합니다.'))
     updates[key]=value
   if node.tag=='image':
    images=doc.by_guid[self.guid].child('componentimages');ids={n.get('this') for n in images.children} if images else set()
    if editor.values.get('componentimage') not in ids:raise ValueError(tr('componentimage는 이 컴포넌트의 이미지 GUID를 선택하세요.'))
   if updates:changes.append((node,updates))
  if changes:self.source=doc.patch(changes);self.render()
 def sync_images(self):
  desired={node.get('this'):get() for node,key,get in self.owner.inputs if node.tag=='component_image' and key=='imagepath'}
  doc=Document(self.source);images=doc.by_guid[self.guid].child('componentimages')
  updates=[(n,{'imagepath':desired[n.get('this')]}) for n in images.children if n.get('this') in desired and n.get('imagepath','')!=desired[n.get('this')]] if images is not None else []
  if updates:
   if not self.checked_flush():return
   doc=Document(self.source);images=doc.by_guid[self.guid].child('componentimages')
   self.source=doc.patch([(n,{'imagepath':desired[n.get('this')]}) for n in images.children if n.get('this') in desired]);self.render()
 def checked_flush(self):
  try:self.flush();return True
  except ValueError as e:messagebox.showerror(tr('상태 속성 확인'),str(e),parent=self.owner);return False
 def render(self):
  for w in self.body.winfo_children():w.destroy()
  self.groups=[];doc=Document(self.source);c=doc.by_guid[self.guid];items,self.template_mode=state_items(c)
  for button in self.state_buttons:button.configure(state='disabled' if self.template_mode else 'normal')
  self.state_ids=[s.get('uniqueguid') if self.template_mode else s.get('this') for s in items];self.choice.configure(values=[s.get('name',s.tag)+' · '+(s.get('uniqueguid','') if self.template_mode else s.get('this',''))[:8] for s in items])
  if self.selected not in self.state_ids:self.selected=self.state_ids[0] if self.state_ids else None
  if self.selected is not None:self.choice.current(self.state_ids.index(self.selected))
  else:self.choice.set('')
  names={s.get('this'):s.get('name',s.tag) for s in items}
  self.status.configure(text=tr('현재: ')+names.get(c.get('currentstate'),tr('(없음)'))+tr(' / 기본: ')+names.get(c.get('defaultstate'),tr('(없음)')))
  state=state_node(doc,self.guid,self.selected)
  if hasattr(self.owner,'refresh_state_navigation'):self.owner.after_idle(self.owner.refresh_state_navigation)
  if self.template_mode:
   self.render_template(doc,c);return
  if state is None:return
  ttk.Label(self.body,text='this = '+state.get('this',''),wraplength=470).pack(fill='x')
  self.group(state,tr('상태 속성'),'state')
  metrics=state.child('imagemetrics');images=c.child('componentimages');self.image_ids=[i.get('this') for i in images.children] if images else []
  imagepaths={i.get('this'):i.get('imagepath','') for i in images.children} if images else {}
  if metrics:
   for index,node in enumerate(metrics.children,1):
    ttk.Label(self.body,text=f'imagemetrics {index} → '+imagepaths.get(node.get('componentimage'),tr('(연결 이미지 없음)')),wraplength=470).pack(fill='x')
    self.group(node,f'imagemetrics / image {index}','image',imagepaths)

  ttk.Button(self.body,text=tr('이미지 메트릭 추가'),command=lambda:self.add_child('image')).pack(anchor='w')
  text=state.child('component_text')
  if text is not None:self.group(text,tr('component_text · 텍스트 속성'),'text')
  else:ttk.Button(self.body,text=tr('component_text 추가'),command=lambda:self.add_child('text')).pack(anchor='w')
  for child in state.children:
   if child.tag in ('imagemetrics','component_text'):continue
   for index,node in enumerate(child.descendants(),1):
    if node.attrs:self.group(node,f'{child.tag} / {node.tag} {index}','extra')
 def group(self,node,title,kind,paths=None):
  catalog=dict(self.catalog['extra'].get(node.tag,{}) if kind=='extra' else self.catalog[kind]);catalog.update({k:[v] for k,v in node.attrs.items() if k not in catalog})
  if paths is not None:catalog['componentimage']=list(paths) or ['']
  editor=ComponentOptions(self.body,node,title=title,reserved={'this','uniqueguid'},pair_docking=False,catalog=catalog,required={"componentimage"} if kind=="image" else None,allow_custom=True)
  self.groups.append((node,editor))
  if kind=='image':
   from image_rows import thumbnail
   preview=thumbnail(editor,self.owner,(paths or {}).get(node.get('componentimage'),''))
   original_change=editor.change
   def change(key,value,original=original_change,canvas=preview,imagepaths=paths):
    original(key,value)
    if key=='componentimage':thumbnail(editor,self.owner,imagepaths.get(value,''),canvas)
   editor.change=change
  if kind!='state':
   doc=Document(self.source);state=state_node(doc,self.guid,self.selected);index=next(i for i,n in enumerate(state.descendants()) if n.start==node.start)
   ttk.Button(editor,text=tr('항목 삭제'),command=lambda i=index:self.remove_child(i)).pack(anchor='e')
 def select(self,e=None):
  index=self.choice.current()
  if not self.checked_flush():
   if self.selected in self.state_ids:self.choice.current(self.state_ids.index(self.selected))
   return
  self.selected=self.state_ids[index];self.render()
 def commit_local(self,source,selected=None):
  if source==self.source:return
  self.history.append((self.source,self.selected));self.future.clear();self.source=source
  if selected:self.selected=selected
  self.owner.last_history=self.travel;self.render()
 def add(self,copy):
  if self.template_mode:return
  if not self.checked_flush():return
  source,guid=add_state(self.source,self.guid,self.selected if copy else None);self.commit_local(source,guid)
 def remove(self):
  if self.template_mode:return
  if self.selected and self.checked_flush():self.commit_local(remove_state(self.source,self.guid,self.selected))
 def remove_child(self,index):
  if self.checked_flush():self.commit_local(remove_state_child(self.source,self.guid,self.selected,index))
 def use(self,key):
  if self.template_mode:return
  if not self.selected or not self.checked_flush():return
  doc=Document(self.source);self.commit_local(doc.patch([(doc.by_guid[self.guid],{key:self.selected})]))
 def add_child(self,kind):
  if self.template_mode:return
  if not self.checked_flush():return
  try:self.commit_local(add_state_child(self.source,self.guid,self.selected,kind,self.image_ids[0] if self.image_ids else None))
  except ValueError as e:messagebox.showinfo(tr('상태 항목'),str(e),parent=self.owner)
 def travel(self,redo=False):
  stack=self.future if redo else self.history
  if not stack:return 'break'
  if not self.checked_flush():return 'break'
  other=self.history if redo else self.future;other.append((self.source,self.selected));self.source,self.selected=stack.pop();self.render();return 'break'
 def apply_to(self,source):
  self.flush()
  if self.source==self.initial:return source
  if self.template_mode:return merge_template_texts(source,self.source,self.initial,self.guid)
  return merge_states(source,self.source,self.guid)
 def render_template(self,doc,c):
  self.status.configure(text=tr('템플릿에서 가져온 상태 · 현재 XML의 이름/GUID는 읽기 전용'))
  controls=ttk.Frame(self.body);controls.pack(fill='x')
  def refresh():
   if not self.checked_flush():return
   self.owner.app.template_index=None;self.render()
  ttk.Button(controls,text=tr('템플릿 새로고침'),command=refresh).pack(side='right')
  refs=c.child('state_uniqueguids');ref=next((n for n in refs.children if n.get('uniqueguid')==self.selected),None)
  if ref is None:return
  ttk.Label(self.body,text=tr('사용처 GUID: ')+ref.get('uniqueguid',''),wraplength=470).pack(fill='x')
  index=template_index(self.owner.app);match=index.resolve(doc,self.guid)
  if match:
   path,component=match;states=component.find('states')
   original=next((n for n in states if n.get('name')==ref.get('name')),None) if states is not None else None
   ttk.Label(self.body,text=tr('템플릿: ')+path.name,wraplength=470).pack(fill='x')
   if original is not None:
    ttk.Label(self.body,text=tr('원본 상태 GUID: ')+original.get('this',''),wraplength=470).pack(fill='x')
    ttk.Label(self.body,text=tr('템플릿 원본 값 · 읽기 전용 · 최종 적용값과 다를 수 있습니다.'),wraplength=470).pack(fill='x')
    area=ttk.Frame(self.body);area.pack(fill='x');box=tk.Text(area,height=10,width=50,wrap='none')
    sy=ttk.Scrollbar(area,orient='vertical',command=box.yview);sx=ttk.Scrollbar(area,orient='horizontal',command=box.xview)
    area.columnconfigure(0,weight=1);box.grid(row=0,column=0,sticky='ew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew')
    box.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
    image_ids={n.get('componentimage') for n in original.findall('./imagemetrics/*')}
    paths=['%s = %s'%(n.get('this',''),n.get('imagepath','')) for n in component.findall('./componentimages/*') if n.get('this') in image_ids]
    box.insert('1.0',ET.tostring(original,encoding='unicode').strip()+'\n\n'+'\n'.join(paths));box.configure(state='disabled')
   else:ttk.Label(self.body,text=tr('템플릿 원본에 같은 이름의 상태가 없습니다.'),wraplength=470).pack(fill='x')
  else:
   notice=tr('원본 UI 폴더의 templates를 찾을 수 없습니다. 경로 설정을 확인하세요.') if not index.available else tr('원본 상태를 확정할 수 없습니다. 템플릿 누락 또는 중복 정의를 확인하세요.')
   ttk.Label(self.body,text=notice,wraplength=470).pack(fill='x')
  if index.errors:ttk.Label(self.body,text=tr('일부 템플릿을 읽지 못했습니다. 원본 파일을 확인하고 새로고침하세요.'),wraplength=470).pack(fill='x')
  texts=c.child('localised_texts');found=False
  if texts is not None:
   for node in texts.children:
    if node.get('state')!=ref.get('name'):continue
    found=True
    catalog={'text':[''],'text_label':[''],'is_text_localised':['true','false']}
    catalog.update({k:[v] for k,v in node.attrs.items() if k!='state'})
    editor=ComponentOptions(self.body,node,title=tr('현재 XML의 상태별 텍스트'),reserved={'state'},pair_docking=False,catalog=catalog)
    self.groups.append((node,editor))
  if not found:ttk.Label(self.body,text=tr('현재 XML에 이 상태의 텍스트 항목이 없습니다.'),wraplength=470).pack(fill='x')
