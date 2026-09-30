from i18n import tr, trf
import tkinter as tk
from tkinter import ttk

def info_text(doc,guid):
 if not doc or guid not in doc.by_guid:return tr('컴포넌트를 선택하세요.')
 node=doc.by_guid[guid];lines=[]
 def section(title,items):
  lines.append('['+title+']')
  lines.extend(f'{key} = {value}' for key,value in items);lines.append('')
 section(tr('컴포넌트'),node.attrs.items())
 layout=node.child('LayoutEngine')
 if layout is not None:
  section(tr('레이아웃 엔진 · LayoutEngine'),layout.attrs.items())
  for child in layout.children:
   section('LayoutEngine / '+child.tag,child.attrs.items())
   for i,entry in enumerate(child.children,1):section(f'{child.tag} / {entry.tag} {i}',entry.attrs.items())
 state=doc.state(node)
 if state:
  section(tr('현재 상태'),state.attrs.items())
  text=state.child('component_text')
  if text:section(tr('텍스트'),text.attrs.items())
 images=node.child('componentimages')
 if images:
  for i,image in enumerate(images.children,1):section(trf('이미지 {0}', i),image.attrs.items())
 callbacks=node.child('callbackwithcontextlist')
 if callbacks:
  for i,callback in enumerate(callbacks.children,1):section(trf('콜백 {0}', i),callback.attrs.items())
 return '\n'.join(lines)

class ComponentInfo(ttk.Frame):
 def __init__(self,parent):
  super().__init__(parent,padding=4);self.place(relx=1,x=-8,y=8,anchor='ne',relwidth=.30,relheight=.94)
  header=ttk.Frame(self);header.pack(fill='x');ttk.Label(header,text=tr('컴포넌트 정보 · 읽기 전용')).pack(side='left')
  self.folded=False;ttk.Button(header,text='− / +',width=5,command=self.toggle).pack(side='right')
  self.body=ttk.Frame(self);self.body.pack(fill='both',expand=True)
  self.text=tk.Text(self.body,wrap='word',font=('Consolas',9),spacing1=0,spacing2=0,spacing3=0,padx=4,pady=4,bg='#20252c',fg='#d8dfe8',relief='flat',state='disabled')
  self.body.columnconfigure(0,weight=1);self.body.columnconfigure(1,minsize=18);self.body.rowconfigure(0,weight=1)
  self.text.grid(row=0,column=0,sticky='nsew');bar=ttk.Scrollbar(self.body,orient='vertical',command=self.text.yview);bar.grid(row=0,column=1,sticky='ns');self.text.configure(yscrollcommand=bar.set)
  self.last=None
 def toggle(self):
  self.folded=not self.folded
  if self.folded:self.body.pack_forget();self.place_configure(relheight=0,height=36)
  else:self.body.pack(fill='both',expand=True);self.place_configure(relheight=.94,height=0)
 def update_info(self,doc,guid):
  content=info_text(doc,guid)
  if content==self.last:return
  self.last=content;self.text.configure(state='normal');self.text.delete('1.0','end');self.text.insert('1.0',content);self.text.configure(state='disabled')
