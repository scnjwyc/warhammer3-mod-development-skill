from i18n import tr, trf
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from PIL import Image,ImageTk
from edit_support import bind_entry_history

def image_visible(hidden,component,image):return (component,image) not in hidden

def build_images(owner,parent,images):
 from inspector import resource_relative
 app=owner.app
 if not hasattr(app,'hidden_images'):app.hidden_images=set()
 group=ttk.LabelFrame(parent,text=tr('이미지'),padding=4);group.pack(fill='x',pady=4)
 for index,node in enumerate(images.children):
  row=ttk.Frame(group);row.pack(fill='x',pady=2);row.columnconfigure(1,weight=1)
  if hasattr(owner,'anchor'):owner.anchor('images',trf('이미지 {0}', index + 1),row)
  ttk.Label(row,text=str(index+1),width=2).grid(row=0,column=0)
  var=tk.StringVar(value=node.get('imagepath',''));entry=ttk.Entry(row,textvariable=var);entry.grid(row=0,column=1,sticky='ew');bind_entry_history(entry,var)
  owner.inputs.append((node,'imagepath',var.get))
  def browse(v=var):
   path=filedialog.askopenfilename(parent=owner,filetypes=[(tr('이미지'),'*.png *.jpg *.dds'),(tr('모든 파일'),'*.*')])
   if not path:return
   relative=resource_relative(path,app.resources.roots)
   if relative:v.set(relative)
   else:messagebox.showinfo(tr('리소스 경로'),tr('설정된 추출 리소스 폴더 내부의 이미지를 선택하세요.'),parent=owner)
  ttk.Button(row,text='...',width=3,command=browse).grid(row=0,column=2,padx=2)
  preview=tk.Canvas(row,width=48,height=48,bg='#242831',highlightthickness=0);preview.grid(row=0,column=3,padx=2)
  def refresh(*args,v=var,canvas=preview):
   canvas.delete('all');canvas.photo=None
   path=app.resources.resolve(v.get())
   try:
    if path is None:raise OSError()
    with Image.open(path) as source:
     im=source.convert('RGBA');im.thumbnail((44,44))
    canvas.photo=ImageTk.PhotoImage(im,master=canvas);canvas.create_image(24,24,image=canvas.photo)
   except (OSError,ValueError):canvas.create_text(24,24,text=tr('없음'),fill='#b7bdc5',font=('',8))
  var.trace_add('write',refresh);refresh()
  eye=tk.Canvas(row,width=28,height=28,highlightthickness=1,highlightbackground='#888888',takefocus=True);eye.grid(row=0,column=4,padx=2)
  guid=node.get('this') or node.get('uniqueguid','')
  guidrow=ttk.Frame(row);guidrow.grid(row=1,column=1,columnspan=4,sticky='ew',pady=(2,4));guidrow.columnconfigure(0,weight=1)
  guidentry=ttk.Entry(guidrow);guidentry.insert(0,guid);guidentry.configure(state='readonly');guidentry.grid(row=0,column=0,sticky='ew')
  def copy_guid(value=guid):owner.clipboard_clear();owner.clipboard_append(value)
  ttk.Button(guidrow,text=tr('GUID 복사'),command=copy_guid).grid(row=0,column=1,padx=2)
  key=(owner.guid,node.get('this'))
  def paint(canvas=eye,k=key):
   canvas.delete('all');on=k not in app.hidden_images
   color='#245877' if on else '#888888';canvas.create_oval(3,8,25,21,outline=color,width=2);canvas.create_oval(11,11,17,18,fill=color,outline=color)
   if not on:canvas.create_line(3,25,25,3,fill='#b44949',width=2)
  def toggle(e=None,k=key,draw=paint):
   if k in app.hidden_images:app.hidden_images.remove(k)
   else:app.hidden_images.add(k)
   draw();app.draw();return 'break'
  eye.bind('<Button-1>',toggle);eye.bind('<space>',toggle);paint()
  from component_options import ComponentOptions
  if hasattr(owner,'extra_groups'):
   extra=ComponentOptions(group,node,title=trf('이미지 {0} 추가 옵션', index + 1),reserved={'this','uniqueguid','imagepath'},pair_docking=False,catalog={},allow_custom=True)
   owner.extra_groups.append((node,extra))
  if hasattr(owner,'structural'):ttk.Button(row,text=tr('삭제'),command=lambda i=index:owner.structural('componentimages','remove',i)).grid(row=2,column=4)
 return group


def thumbnail(parent,owner,path,canvas=None):
 if canvas is None:
  canvas=tk.Canvas(parent,width=64,height=64,bg='#242831',highlightthickness=0);canvas.pack(anchor='w',padx=8,pady=3)
 canvas.delete('all');canvas.photo=None
 asset=owner.app.resources.resolve(path) if path else None
 try:
  if asset is None:raise OSError()
  with Image.open(asset) as source:
   im=source.convert('RGBA');im.thumbnail((60,60))
  canvas.photo=ImageTk.PhotoImage(im,master=canvas);canvas.create_image(32,32,image=canvas.photo)
 except (OSError,ValueError):canvas.create_text(32,32,text=tr('이미지 없음'),fill='#b7bdc5',font=('',8))
 return canvas
