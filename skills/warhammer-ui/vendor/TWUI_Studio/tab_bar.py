"""Natural-width document tabs inside a clipped viewport, without a scrollbar."""
import tkinter as tk
from tkinter import ttk

class DocumentTabs(ttk.Frame):
 def __init__(self,parent,close):
  super().__init__(parent)
  self.close_command=close;self.pressed=None;self._layout_job=None;self._reveal=False
  self._width=1;self._overflow=False;self._destroying=False;self._reveal_job=None
  style=ttk.Style(parent)
  self.close_icon=tk.PhotoImage(master=self,width=14,height=14)
  for i in range(4,10):
   self.close_icon.put('#ba4545',(i,i));self.close_icon.put('#ba4545',(13-i,i))
  name='Document'+str(id(self));close_element=name+'.close';notebook_style=name+'.TNotebook'
  style.element_create(close_element,'image',self.close_icon,border=2,sticky='')
  style.layout(notebook_style+'.Tab',[('Notebook.tab',{'sticky':'nswe','children':[('Notebook.padding',{'side':'top','sticky':'nswe','children':[('Notebook.focus',{'side':'top','sticky':'nswe','children':[('Notebook.label',{'side':'left','sticky':''}),(close_element,{'side':'left','sticky':''})]})]})]})])
  self.columnconfigure(0,weight=1)
  self.left=ttk.Button(self,text='<',width=2,command=lambda:self.scroll(-120),takefocus=False)
  self.right=ttk.Button(self,text='>',width=2,command=lambda:self.scroll(120),takefocus=False)
  self.viewport=tk.Canvas(self,highlightthickness=0,borderwidth=0,width=1,height=1)
  self.viewport.grid(row=0,column=0,sticky='ew')
  self.notebook=ttk.Notebook(self.viewport,height=1,style=notebook_style,takefocus=False)
  self.notebook_id=self.viewport.create_window(0,0,anchor='nw',window=self.notebook)
  self.notebook.bind('<ButtonPress-1>',self.press)
  self.notebook.bind('<ButtonRelease-1>',self.release)
  self.notebook.bind('<Button-3>',self._context_menu)
  self.notebook.bind('<<NotebookTabChanged>>',self._changed)
  self.notebook.bind('<Configure>',lambda e:self._schedule())
  self.viewport.bind('<Configure>',lambda e:self._schedule())
  self.bind('<<ThemeChanged>>',lambda e:self._schedule())
  for widget in (self,self.viewport,self.notebook,self.left,self.right):
   widget.bind('<MouseWheel>',self.wheel)
   widget.bind('<Button-4>',lambda e:self.wheel(e,-60))
   widget.bind('<Button-5>',lambda e:self.wheel(e,60))

 def _schedule(self,reveal=False):
  if self._destroying:return
  self._reveal=self._reveal or reveal
  if self._layout_job is None:self._layout_job=self.after_idle(self._layout)

 def _layout(self):
  self._layout_job=None
  natural=self.notebook.winfo_reqwidth();overflow=natural>self.winfo_width()
  if overflow!=self._overflow:
   self._overflow=overflow
   if overflow:
    self.left.grid(row=0,column=1,sticky='ns');self.right.grid(row=0,column=2,sticky='ns')
   else:self.left.grid_remove();self.right.grid_remove()
  width=max(natural,self.viewport.winfo_width());height=self.notebook.winfo_reqheight()
  self._width=width
  self.viewport.itemconfigure(self.notebook_id,width=width,height=height)
  self.viewport.configure(height=height,scrollregion=(0,0,width,height))
  if self._reveal:
   self._reveal=False
   if self._reveal_job is None:self._reveal_job=self.after_idle(self._ensure_selected)
  self._buttons()

 def _buttons(self):
  first,last=self.viewport.xview()
  self.left.state(['!disabled' if first>0.0001 else 'disabled'])
  self.right.state(['!disabled' if last<0.9999 else 'disabled'])

 def scroll(self,pixels):
  self.viewport.xview_moveto((self.viewport.canvasx(0)+pixels)/max(1,self._width));self._buttons()

 def wheel(self,event,pixels=None):
  if pixels is None:
   delta=getattr(event,'delta',0)
   if not delta:return 'break'
   pixels=-delta/120*60 if abs(delta)>=120 else -delta*6
  self.scroll(pixels)
  return 'break'  # Stop platform Notebook bindings from switching documents.

 def _ensure_selected(self):
  self._reveal_job=None
  if not self.winfo_exists() or not self.select():return
  target=self.index(self.select());count=len(self.tabs())
  if target==count-1:self.viewport.xview_moveto(1)
  else:
   # Binary search actual tab edges, independent of theme/font/icon padding.
   y=max(5,self.notebook.winfo_height()//2)
   def edge(index):
    lo,hi=0,self._width
    while lo<hi:
     mid=(lo+hi)//2
     try:at=self.notebook.index('@%d,%d'%(mid,y))
     except tk.TclError:at=count
     if at<index:lo=mid+1
     else:hi=mid
    return lo
   left,right=edge(target),edge(target+1)
   start=self.viewport.canvasx(0);visible=self.viewport.winfo_width()
   if left<start or right-left>visible:self.viewport.xview_moveto(left/self._width)
   elif right>start+visible:self.viewport.xview_moveto((right-visible)/self._width)
  self._buttons()

 def _changed(self,event):
  self._schedule(reveal=True);self.event_generate('<<NotebookTabChanged>>')

 def _context_menu(self,event):
  self.event_generate('<Button-3>',x=event.x_root-self.winfo_rootx(),y=event.y_root-self.winfo_rooty(),rootx=event.x_root,rooty=event.y_root)
  return 'break'

 def add(self,child,**options):
  self.notebook.add(child,**options);child.bind('<Destroy>',lambda e:self._schedule(),add='+');self._schedule()

 def tabs(self):return self.notebook.tabs()

 def select(self,tab_id=None):
  if tab_id is None:return self.notebook.select()
  result=self.notebook.select(tab_id);self._schedule(reveal=True);return result

 def tab(self,tab_id,option=None,**options):
  result=self.notebook.tab(tab_id,option,**options)
  if options:self._schedule()
  return result

 def index(self,tab_id):
  if isinstance(tab_id,str) and tab_id.startswith('@'):
   x,y=map(int,tab_id[1:].split(','))
   x+=self.winfo_rootx()-self.notebook.winfo_rootx();y+=self.winfo_rooty()-self.notebook.winfo_rooty()
   tab_id='@%d,%d'%(x,y)
  return self.notebook.index(tab_id)

 def press(self,event):
  if 'close' in self.notebook.identify(event.x,event.y):
   self.pressed=self.notebook.tabs()[self.notebook.index('@%d,%d'%(event.x,event.y))];return 'break'

 def release(self,event):
  pressed=self.pressed;self.pressed=None
  if pressed is not None:
   if 'close' in self.notebook.identify(event.x,event.y):
    index=self.notebook.index('@%d,%d'%(event.x,event.y))
    if self.tabs()[index]==pressed:self.close_command(index)
   return 'break'

 def destroy(self):
  self._destroying=True
  if self._reveal_job is not None:self.after_cancel(self._reveal_job);self._reveal_job=None
  if self._layout_job is not None:self.after_cancel(self._layout_job);self._layout_job=None
  super().destroy()
