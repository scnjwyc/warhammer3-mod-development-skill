from i18n import tr, trf
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from edit_support import History
from layout_geometry import unsupported_docking_options,component_format
from inspector_scroll import install_scrolling

RESERVED={'this','id','uniqueguid','currentstate','defaultstate','offset','tooltiplabel'}
def load_catalog(path):
 # Packaged JSON is UTF-8 regardless of the Windows system locale.
 try:
  catalog=json.loads(Path(path).read_text(encoding='utf-8-sig'))
  if not isinstance(catalog,dict) or any(not isinstance(k,str) or not isinstance(v,list) or not v or any(not isinstance(item,str) for item in v) for k,v in catalog.items()):
   raise ValueError(tr('옵션 목록 형식이 올바르지 않습니다.'))
  return catalog,None
 except (OSError,UnicodeError,ValueError) as error:
  return {},str(error)

def paired_change(current,key,value):
 values=dict(current)
 if key in ('docking','dock_offset'):
  if value is None:
   values.pop('docking',None);values.pop('dock_offset',None);values.pop('component_anchor_point',None)
  else:
   values.setdefault('docking','Top Left')
   values.setdefault('dock_offset','0,0');values[key]=value
   if key=='docking' and current.get('docking')!=value:
    from layout_geometry import docking_anchor
    from model import Node
    ax,ay=docking_anchor(Node('component',0,0,{'docking':value}))
    values['component_anchor_point']=f'{ax:.2f},{ay:.2f}'
 elif value is None:values.pop(key,None)
 else:values[key]=value
 return values

class ComponentOptions(ttk.LabelFrame):
 def __init__(self,parent,node,title=tr('컴포넌트 옵션'),catalog_file="component_options.json",reserved=None,pair_docking=True,catalog=None,required=None,allow_custom=False):
  super().__init__(parent,text=title,padding=8);self.allow_custom=allow_custom;self.reserved=RESERVED if reserved is None else reserved;self.required=set(required or ());self.pair_docking=pair_docking;self.pack(fill='x',pady=6)
  self.blocked=unsupported_docking_options(node) if pair_docking else set()
  if self.blocked:
   guidance='Template instance: dock_point + offset' if component_format(node)=='template' else 'Component definition: docking + dock_offset'
   ttk.Label(self,text=guidance,wraplength=450).pack(fill='x')
  self.catalog,catalog_error=load_catalog(Path(__file__).parent/catalog_file)
  if catalog is not None:self.catalog=catalog;catalog_error=None
  if catalog_error:ttk.Label(self,text=tr('옵션 후보 파일을 읽지 못했습니다. 기존 속성은 편집할 수 있습니다.'),wraplength=450).pack(fill='x')
  self.initial={k:v for k,v in node.attrs.items() if k not in self.reserved};self.history=History(dict(self.initial));self.values=dict(self.initial)
  for key in self.required:self.values.setdefault(key,'')
  row=ttk.Frame(self);row.pack(fill='x');self.query=tk.StringVar();self.search=ttk.Combobox(row,textvariable=self.query);self.search.pack(side='left',fill='x',expand=True)
  self.search.bind('<KeyRelease>',lambda e:self.candidates());ttk.Button(row,text='+',width=3,command=self.add).pack(side='right')
  self.rows=ttk.Frame(self);self.rows.pack(fill='x');self.render()
 def candidates(self):self.search.configure(values=[k for k in sorted(self.catalog) if k not in self.blocked and k not in self.reserved and k not in self.values and self.query.get().casefold() in k.casefold()])
 def change(self,key,value):
  if value is not None and key in self.blocked:return
  if key in self.required and value is None:return
  values=dict(self.values)
  if self.pair_docking:values=paired_change(values,key,value)
  elif value is None:values.pop(key,None)
  else:values[key]=value
  self.history.record(values);self.values=values;self.winfo_toplevel().last_history=self.travel
 def add(self):
  key=self.query.get()
  if key=='dock_position' or key in self.blocked or key in self.reserved or key in self.values:return
  if key not in self.catalog:
   import re
   if not self.allow_custom or not re.fullmatch(r'[A-Za-z_][\w.-]*',key):return
  observed=self.catalog.get(key,['']);self.change(key,'false' if set(observed)<= {'true','false'} else ('0,0' if key=='dock_offset' else observed[0]));self.query.set('');self.render()
 def remove(self,key):self.change(key,None);self.render();self.focus_set()
 def travel(self,redo=False):
  if not (self.history.future if redo else self.history.past):return 'break'
  self.values=dict(self.history.redo() if redo else self.history.undo());self.render();return 'break'
 def render(self):
  for key in self.required:self.values.setdefault(key,'')
  for w in self.rows.winfo_children():w.destroy()
  for key,value in sorted(self.values.items(),key=lambda item:item[0] not in self.required):
   if key in getattr(self,"custom_keys",set()):continue
   row=ttk.Frame(self.rows);row.pack(fill='x',pady=3);ttk.Label(row,text=key,width=27).pack(side='left');ttk.Label(row,text=tr('필수'),width=4).pack(side='left') if key in self.required else ttk.Button(row,text='×',width=2,command=lambda k=key:self.remove(k)).pack(side='left')
   values=self.catalog.get(key,[]);boolean=set(values)<= {'true','false'} and bool(values)
   v=tk.StringVar(value=value);entry=ttk.Combobox(row,textvariable=v,values=['false','true'] if boolean else sorted(set(values+[value])),state='disabled' if key in self.blocked else 'readonly' if boolean or key=='docking' else 'normal');entry.pack(side='left',fill='x',expand=True)
   v.trace_add('write',lambda *a,k=key,var=v:self.change(k,var.get()))
   if key=='docking':entry.bind('<<ComboboxSelected>>',lambda e:self.render())
   entry.bind('<Control-z>',lambda e:self.travel());entry.bind('<Control-Shift-Z>',lambda e:self.travel(True));entry.bind('<Control-y>',lambda e:self.travel(True))
   entry.bind('<MouseWheel>',lambda e:'break')
  self.candidates()
  self.after_idle(lambda:install_scrolling(self.winfo_toplevel()))
 def clear(self):
  self.history.record({});self.values={};self.winfo_toplevel().last_history=self.travel;self.render()
 def changes(self):return {k:self.values.get(k) for k in self.initial.keys()|self.values.keys() if self.initial.get(k)!=self.values.get(k)}
