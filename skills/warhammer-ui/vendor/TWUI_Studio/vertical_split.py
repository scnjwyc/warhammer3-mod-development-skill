import tkinter as tk

def bounded_fraction(value):return max(.25,min(.75,value))
class VerticalSplit(tk.Frame):
 def __init__(self,parent):
  super().__init__(parent);self.panes=[];self.fraction=.6;self.guide=None
  self.handle=tk.Frame(self,height=6,bg='#a5a5a5',cursor='sb_v_double_arrow');self.handle.bind('<ButtonPress-1>',self.start);self.handle.bind('<B1-Motion>',self.move);self.handle.bind('<ButtonRelease-1>',self.release);self.bind('<Configure>',lambda e:self.layout())
 def add(self,pane):self.panes.append(pane);self.layout()
 def layout(self):
  if len(self.panes)!=2:return
  h=self.winfo_height();y=round(h*self.fraction);self.panes[0].place(x=0,y=0,relwidth=1,height=max(1,y-3));self.panes[1].place(x=0,y=y+3,relwidth=1,height=max(1,h-y-3));self.handle.place(x=0,y=y-3,relwidth=1,height=6);self.handle.lift()
 def start(self,e):self.guide=tk.Frame(self,bg='#247b91');self.move(e)
 def move(self,e):
  if self.guide is None:return
  self.target=bounded_fraction((e.y_root-self.winfo_rooty())/max(1,self.winfo_height()));self.guide.place(x=0,y=round(self.target*self.winfo_height()),relwidth=1,height=3);self.guide.lift()
 def release(self,e):
  if self.guide is None:return
  self.move(e);self.fraction=self.target;self.guide.destroy();self.guide=None;self.layout()
