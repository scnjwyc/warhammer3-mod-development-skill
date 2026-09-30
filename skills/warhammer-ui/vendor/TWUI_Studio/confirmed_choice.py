"""Confirmed-value history and a single-active-field choice editor."""
import tkinter as tk
from tkinter import ttk

class ConfirmedHistory:
 def __init__(self,value):
  self.values=[value];self.accepted=0;self.position=0;self.draft=value;self.saved_draft=None
 @property
 def committed(self):return self.values[self.accepted]
 def edit(self,value):self.draft=value;self.position=None;self.saved_draft=None
 def can_preview(self,step):
  if step<0 and self.position is None and self.draft!=self.committed:return True
  if step>0 and self.saved_draft is not None and self.position==self.accepted:return True
  current=self.accepted if self.position is None else self.position
  return 0<=current+step<len(self.values)
 def preview(self,step):
  if step<0 and self.position is None and self.draft!=self.committed:
   self.saved_draft=self.draft;self.position=self.accepted;self.draft=self.committed;return self.draft
  if step>0 and self.saved_draft is not None and self.position==self.accepted:
   self.draft=self.saved_draft;self.saved_draft=None;self.position=None;return self.draft
  current=self.accepted if self.position is None else self.position
  self.position=max(0,min(len(self.values)-1,current+step));self.draft=self.values[self.position]
  return self.draft
 def cancel(self):self.saved_draft=None;self.position=self.accepted;self.draft=self.committed;return self.draft
 def confirm(self):
  self.saved_draft=None
  if self.position is not None and self.draft==self.values[self.position]:self.accepted=self.position
  elif self.draft!=self.committed:
   self.values=self.values[:self.accepted+1]+[self.draft];self.accepted=len(self.values)-1
  self.position=self.accepted;return self.committed

class ConfirmedChoice:
 def __init__(self,owner,parent,row,value,options):
  self.owner=owner;self.history=ConfirmedHistory(value);self.options=options;self.busy=False;self.history_preview=False
  self.var=tk.StringVar(value=value)
  self.entry=ttk.Entry(row,textvariable=self.var);self.entry.pack(side='left',fill='x',expand=True)
  self.entry._input_completion_managed=True
  self.entry.bind('<KP_Enter>',self.confirm)
  self.arrow=ttk.Button(row,text='▼',width=3,takefocus=False,command=self.show_all);self.arrow.pack(side='right')
  self.list_area=ttk.Frame(parent)
  self.box=tk.Listbox(self.list_area,height=6,exportselection=False,takefocus=False,relief='flat',borderwidth=0)
  self.box.pack(side='left',fill='both',expand=True)
  self.scrollbar=ttk.Scrollbar(self.list_area,orient='vertical',command=self.box.yview,takefocus=False);self.scrollbar.pack(side='right',fill='y');self.scrollbar._wheel_target=self.box
  self.box.configure(yscrollcommand=self.scrollbar.set)
  self.parent=parent;self.row=row
  self.entry.bind('<FocusIn>',self.activate);self.entry.bind('<FocusOut>',lambda e:self.entry.after_idle(self.check_focus))
  self.entry.bind('<Button-1>',self.activate,add='+')
  self.entry.bind('<Escape>',self.escape);self.entry.bind('<Tab>',self.tab);self.entry.bind('<Shift-Tab>',lambda e:self.tab(e,True))
  self.entry.bind('<ISO_Left_Tab>',lambda e:self.tab(e,True))
  self.entry.bind('<Return>',self.confirm)
  self.entry.bind('<Control-z>',lambda e:self.travel(-1));self.entry.bind('<Control-Shift-Z>',lambda e:self.travel(1));self.entry.bind('<Control-y>',lambda e:self.travel(1))
  self.entry.bind('<Down>',lambda e:self.move(1));self.entry.bind('<Up>',lambda e:self.move(-1))
  self.box.bind('<Button-1>',self.mouse_pick)
  for widget in (self.entry,self.arrow):
   for seq in ('<MouseWheel>','<Button-4>','<Button-5>'):widget.bind(seq,lambda e:'break')
  self.var.trace_add('write',self.changed)
 def get(self):return self.history.committed
 def active(self):return getattr(self.owner,'active_choice',None) is self
 def activate(self,event=None):
  old=getattr(self.owner,'active_choice',None)
  if old is not self:
   if old:old.cancel()
   self.owner.active_choice=self
 def check_focus(self):
  if not self.entry.winfo_exists():return
  if self.active() and self.owner.focus_get() not in (self.entry,self.arrow,self.box,self.scrollbar):self.cancel()
 def set_value(self,value):
  self.busy=True
  try:self.var.set(value);self.entry.icursor('end')
  finally:self.busy=False
 def cancel(self):
  self.set_value(self.history.cancel());self.history_preview=False;self.list_area.pack_forget()
  if self.active():self.owner.active_choice=None
 def release_focus(self):
  self.entry.selection_clear()
  if self.active():self.owner.active_choice=None
  self.owner.focus_set()
 def escape(self,e=None):self.cancel();self.release_focus();return 'break'
 def tab(self,e=None,back=False):
  target=self.entry.tk_focusPrev() if back else self.entry.tk_focusNext()
  self.cancel();target.focus_set();return 'break'
 def changed(self,*args):
  if self.busy:return
  if not self.active():self.set_value(self.history.committed);return
  self.owner.last_history=lambda redo=False:self.travel(1 if redo else -1)
  self.history.edit(self.var.get());self.history_preview=False;self.show_matches()
 def show_matches(self,all_values=False):
  if not self.active():return
  query='' if all_values else self.var.get().casefold()
  values=sorted((v for v in self.options if query in v.casefold()),key=lambda v:(not v.casefold().startswith(query),v))
  self.box.delete(0,'end')
  for v in values:self.box.insert('end',v)
  if values:self.box.selection_set(0);self.list_area.pack(fill='x',after=self.row,pady=(0,6))
  else:self.list_area.pack_forget()
 def show_all(self):
  if self.active() and self.list_area.winfo_manager():return self.escape()
  self.activate();self.entry.focus_set();self.show_matches(True)
 def move(self,delta):
  self.activate()
  if not self.list_area.winfo_manager():self.show_matches()
  if self.box.size():
   sel=self.box.curselection();i=max(0,min(self.box.size()-1,(sel[0] if sel else 0)+delta))
   self.box.selection_clear(0,'end');self.box.selection_set(i);self.box.see(i)
  return 'break'
 def confirm(self,e=None):
  self.owner.last_history=lambda redo=False:self.travel(1 if redo else -1)
  self.activate()
  if not self.history_preview and self.list_area.winfo_manager() and self.box.size():
   sel=self.box.curselection();self.history.edit(self.box.get(sel[0] if sel else 0))
  self.set_value(self.history.confirm());self.history_preview=False;self.list_area.pack_forget();self.release_focus();return 'break'
 def mouse_pick(self,e):
  if not self.active() or not self.box.size():return 'break'
  self.owner.last_history=lambda redo=False:self.travel(1 if redo else -1)
  i=self.box.nearest(e.y);self.history.edit(self.box.get(i));self.set_value(self.history.confirm());self.history_preview=False;self.list_area.pack_forget();self.release_focus();return 'break'
 def travel(self,step):
  if not self.history.can_preview(step):return 'break'
  self.activate();self.set_value(self.history.preview(step));self.history_preview=True;self.list_area.pack_forget();return 'break'
