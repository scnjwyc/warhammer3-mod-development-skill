from i18n import tr, trf
import re
import math
from radial_geometry import ANGLE_KEYS,degrees_to_xml,xml_to_degrees
import tkinter as tk
from tkinter import ttk
from component_options import ComponentOptions

def column_values(value):
 parts=value.split(',')
 if not parts or any(not re.fullmatch(r'\d{1,4}',p.strip()) for p in parts):raise ValueError(tr('열 너비는 0~9999의 정수로 입력하세요.'))
 return [str(int(p.strip())) for p in parts]

def layout_initial_values(node):
 values=dict(node.attrs)
 columns=node.child('columnwidths') if hasattr(node,'child') else None
 if columns is not None:values['columnwidths']=','.join(c.get('width','0') for c in columns.children)
 return values

class LayoutOptions(ComponentOptions):
 def __init__(self,parent,node):
  self.custom_keys={'type','columnwidths'};self.type_row=None;self.column_area=None
  super().__init__(parent,node,title=tr('LayoutEngine 옵션'),catalog_file='layout_options.json',reserved={'type'},pair_docking=False)
  self.initial=layout_initial_values(node);self.values=dict(self.initial);self.history.current=dict(self.initial)
  self.render()
 def change(self,key,value):
  super().change(key,value)
  self.notify_preview()
 def notify_preview(self):
  owner=self.winfo_toplevel()
  if hasattr(owner,'children_buttons'):owner.children_buttons()
  preview=getattr(owner,'radial_preview',None)
  if preview is not None and preview.winfo_exists():preview.schedule()
 def candidates(self):
  self.catalog['columnwidths']=['0']
  super().candidates()
 def render(self):
  owner=self.winfo_toplevel();canvas=getattr(owner,'canvas',None);top=canvas.canvasy(0) if canvas is not None else None
  self.custom_keys={'type','columnwidths'} | (ANGLE_KEYS if self.values.get('type')=='RadialList' else set())
  super().render()
  if self.values.get('type')=='RadialList':self.render_angles()
  if self.type_row is not None:self.type_row.destroy()
  self.type_row=ttk.Frame(self);self.type_row.pack(fill='x',before=self.search.master,pady=4)
  ttk.Label(self.type_row,text=tr('type (필수)'),width=18).pack(side='left')
  value=tk.StringVar(value=self.values.get('type',''))
  choice=ttk.Combobox(self.type_row,textvariable=value,state='readonly',values=['']+sorted(set(self.catalog.get('type',[])+([value.get()] if value.get() else []))))
  choice.pack(side='left',fill='x',expand=True)
  def select(*a):self.change('type',value.get());self.render()
  value.trace_add('write',select)
  choice.bind('<Control-z>',lambda e:self.travel());choice.bind('<Control-Shift-Z>',lambda e:self.travel(True))
  if 'columnwidths' in self.values:
   group=ttk.LabelFrame(self.rows,text='columnwidths',padding=3);group.pack(fill='x',pady=3)
   widths=self.values['columnwidths'].split(',')
   def write(index,value):
    current=self.values['columnwidths'].split(',');current[index]=value;self.change('columnwidths',','.join(current))
   def add():self.change('columnwidths',self.values['columnwidths']+',0');self.render()
   def remove(index):
    current=self.values['columnwidths'].split(',');current.pop(index);self.change('columnwidths',','.join(current) if current else None);self.render()
   for i,width in enumerate(widths):
    row=ttk.Frame(group);row.pack(fill='x',pady=1);ttk.Label(row,text=f'column {i+1} · width',width=24).pack(side='left');v=tk.StringVar(value=width)
    entry=ttk.Entry(row,textvariable=v,width=6,validate='key',validatecommand=(self.register(lambda p:p=='' or p.isdigit() and len(p)<=4),'%P'));entry.pack(side='left')
    v.trace_add('write',lambda *a,index=i,var=v:write(index,var.get()))
    entry.bind('<Control-z>',lambda e:self.travel());entry.bind('<Control-Shift-Z>',lambda e:self.travel(True))
    ttk.Button(row,text='×',width=2,command=lambda index=i:remove(index)).pack(side='left')
   ttk.Button(group,text=tr('열 추가 +'),command=add).pack(side='left');ttk.Button(group,text=tr('columnwidths 제거'),command=lambda:self.remove('columnwidths')).pack(side='right')
  self.update_enabled()
  if top is not None:
   def restore():
    if not canvas.winfo_exists():return
    region=list(map(float,canvas.cget('scrollregion').split()))
    if len(region)==4 and region[3]>region[1]:canvas.yview_moveto((top-region[1])/(region[3]-region[1]))
   self.after_idle(restore)
 def render_angles(self):
  from angle_editor import AngleEditor
  for key in ('starting_angle','arc','spacing'):
   if key not in self.values:continue
   group=ttk.Frame(self.rows);group.pack(fill='x',pady=3)
   heading=ttk.Frame(group);heading.pack(fill='x')
   ttk.Label(heading,text=key).pack(side='left')
   ttk.Button(heading,text='×',width=2,command=lambda k=key:self.remove(k)).pack(side='right')
   editor=AngleEditor(group,self.values[key],lambda value,k=key:self.change(k,value),self.travel)
   editor.pack(fill='x')
  ttk.Label(self.rows,text=tr('각도와 라디안 연동 · 다이얼 드래그로 조절 · arc 0°는 제한 없음'),wraplength=480).pack(fill='x',pady=3)
 def update_enabled(self):
  enabled=bool(self.values.get('type'))
  def enable(widget):
   if isinstance(widget,(ttk.Entry,ttk.Combobox,ttk.Button)):widget.state(['!disabled'] if enabled else ['disabled'])
   for child in widget.winfo_children():enable(child)
  enable(self.search.master);enable(self.rows);self.notify_preview()
