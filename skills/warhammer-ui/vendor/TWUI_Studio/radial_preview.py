"""Illustrative radial layout; angles interpreted as radians, not engine emulation."""
import math
import tkinter as tk
from tkinter import ttk
from i18n import tr
from radial_geometry import geometry, radial_layout
from layout_preview_geometry import radial_guide,list_guide
from model import Document

PREVIEW_COUNT = 5

def limited_zoom(value):return max(.05,min(2.,value))

class RadialPreview(ttk.LabelFrame):
 def __init__(self,parent,owner):
  super().__init__(parent,text=tr('레이아웃 미리보기'),padding=5);self.owner=owner;self.zoom=.5;self.job=None;self.photos=[]
  self.help=tk.StringVar();ttk.Label(self,textvariable=self.help,wraplength=510).pack(fill='x')
  self.status=tk.StringVar();ttk.Label(self,textvariable=self.status).pack(fill='x')
  area=ttk.Frame(self);area.pack(fill='both',expand=True);area.columnconfigure(0,weight=1);area.rowconfigure(0,weight=1)
  self.canvas=tk.Canvas(area,height=270,bg='#232830',highlightthickness=0);self.canvas.grid(row=0,column=0,sticky='nsew');self.canvas._wheel_target=self.canvas
  y=ttk.Scrollbar(area,command=self.canvas.yview);y.grid(row=0,column=1,sticky='ns')
  x=ttk.Scrollbar(area,orient='horizontal',command=self.canvas.xview);x.grid(row=1,column=0,sticky='ew')
  self.canvas.configure(yscrollcommand=y.set,xscrollcommand=x.set)
  for seq in ('<Control-MouseWheel>','<Control-Button-4>','<Control-Button-5>'):self.canvas.bind(seq,self.scale)
  self.canvas.bind('<ButtonPress-2>',lambda e:self.canvas.scan_mark(e.x,e.y))
  self.canvas.bind('<B2-Motion>',lambda e:self.canvas.scan_dragto(e.x,e.y,gain=1))
  self.bind('<Destroy>',self.cancel,add='+');self.schedule()
 def cancel(self,e):
  if e.widget is self and self.job is not None:self.after_cancel(self.job);self.job=None
 def scale(self,e):
  delta=1 if getattr(e,'num',None)==4 or getattr(e,'delta',0)>0 else -1
  zoom=limited_zoom(self.zoom*(1.15 if delta>0 else 1/1.15))
  if zoom!=self.zoom:self.zoom=zoom;self.draw()
  return 'break'
 def schedule(self):
  if self.job is not None:self.after_cancel(self.job)
  self.job=self.after(100,self.draw)
 def draw(self):
  if self.job is not None:self.after_cancel(self.job)
  self.job=None;values=self.owner.layout_options.values;kind=values.get('type')
  if kind not in ('RadialList','List','HorizontalList'):self.pack_forget();return
  if not self.winfo_manager():
   order=getattr(self.owner,'children_order_frame',None)
   self.pack(fill='x',pady=6,**({'before':order} if order is not None and order.winfo_exists() else {}))
  c=self.canvas;c.delete('all');z=self.zoom
  if kind=='RadialList':
   self.help.set(tr('핑크: 설정 반지름 · 노랑: 확장 예시 (숨은 6번 자리 포함)\n휠: 이동 · Ctrl+휠: 확대/축소 (최대 200%)'))
   try:guide=radial_guide(values)
   except (ValueError,OverflowError):self.status.set(tr('미리보기: 유효한 숫자를 입력하세요.'));return
   curve=guide['base_curve']
   c.create_line(*[v*z for p in curve for v in p],fill='#ff8cbd',width=2,arrow='last')
   if guide['expanded_curve'] is not None:
    c.create_line(*[v*z for p in guide['expanded_curve'] for v in p],fill='#ffd65c',width=2,arrow='last')
   for p,label,color in ((curve[0],tr('시작'),'#83e4bf'),(curve[-1],tr('arc 끝'),'#ff8cbd')):
    x,y=p;c.create_line(0,0,x*z,y*z,fill=color,dash=(3,3))
    c.create_text(x*z,y*z-35*z,text=label,fill=color,anchor='s')
   for index,(x,y) in enumerate(guide['points']):
    r=24*z;c.create_oval(x*z-r,y*z-r,x*z+r,y*z+r,fill='#38556e',outline='#ffd65c' if guide['slots']==6 else '#b5cadd',width=2,tags=('virtual_child',))
    c.create_text(x*z,y*z,text=str(index+1),fill='white',font=('',max(8,round(12*z))))
   c.create_line(-5,0,5,0,fill='#ff8cbd');c.create_line(0,-5,0,5,fill='#ff8cbd')
   self.status.set(f'{round(z*100)}% · '+tr('간격')+f": {math.degrees(guide['step']):.2f}° · "+tr('반지름')+f": {guide['radius']:.2f}")
  else:
   self.help.set(tr('1차 자식 순서 · 최대 5개 · List: 위→아래 / HorizontalList: 왼쪽→오른쪽'))
   doc=Document(self.owner.baseline);children=doc.children.get(self.owner.guid,[])
   for index,(child,x,y) in enumerate(list_guide(kind,children)):
    c.create_rectangle(x*z,y*z,(x+100)*z,(y+45)*z,fill='#38556e',outline='#b5cadd',tags=('virtual_child',))
    name=doc.by_guid[child].get('id',child)
    c.create_text((x+50)*z,(y+22)*z,text=f'{index+1}. '+name[:14],width=max(30,95*z),fill='white',font=('',max(7,round(10*z))))
   if not children:c.create_text(0,0,text=tr('1차 자식이 없습니다.'),fill='white')
   self.status.set(f'{round(z*100)}% · {min(5,len(children))} / {len(children)}')
  box=c.bbox('all') or (-100,-100,100,100);w=max(500,c.winfo_width());h=270
  left=min(box[0]-30,-w/2);top=min(box[1]-30,-h/2);right=max(box[2]+30,w/2);bottom=max(box[3]+30,h/2)
  c.configure(scrollregion=(left,top,right,bottom));c.xview_moveto(max(0,(-w/2-left)/(right-left)));c.yview_moveto(max(0,(-h/2-top)/(bottom-top)))
