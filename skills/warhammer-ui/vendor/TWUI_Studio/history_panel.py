from i18n import tr, trf
import tkinter as tk
from tkinter import ttk

class HistoryPanel(ttk.LabelFrame):
 def __init__(self,parent,app):
  super().__init__(parent,text=tr('작업 기록 · 최대 20개'),padding=4);self.app=app
  self.place(relx=1,rely=0,anchor='ne',relwidth=.32,relheight=1)
  self.columnconfigure(0,weight=1);self.rowconfigure(0,weight=1)
  self.tree=ttk.Treeview(self,show='tree',selectmode='browse');self.tree.grid(row=0,column=0,sticky='nsew')
  sb=ttk.Scrollbar(self,command=self.tree.yview);sb.grid(row=0,column=1,sticky='ns');self.tree.configure(yscrollcommand=sb.set)
  self.tree.tag_configure('future',foreground='#909090');self.tree.bind('<ButtonRelease-1>',self.click)
 def refresh(self):
  past=self.app.undo_stack;future=self.app.redo_stack;cursor=len(past)
  self.tree.delete(*self.tree.get_children())
  labels=[tr('기록 시작 상태')]+[s.get('_label',tr('XML 편집')) if isinstance(s,dict) else tr('XML 편집') for s in past]+[s.get('_label',tr('XML 편집')) if isinstance(s,dict) else tr('XML 편집') for s in reversed(future)]
  for i,label in enumerate(labels):self.tree.insert('','end',iid=str(i),text=('▶ ' if i==cursor else '   ')+str(i)+'. '+label,tags=('future',) if i>cursor else ())
  self.tree.selection_set(str(cursor));self.tree.see(str(cursor))
 def click(self,e):
  row=self.tree.identify_row(e.y)
  if row:self.app.history_jump(int(row))
