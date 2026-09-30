from i18n import tr, trf
"""Lazy, read-only browser for an extracted UI resource directory."""
import os,time
from pathlib import Path
import tkinter as tk
from tkinter import ttk,messagebox
from PIL import Image,ImageTk
from file_icons import make_icons,file_kind
from model import clean_resource_path,resource_root

class ResourceBrowser(ttk.LabelFrame):
 def __init__(self,parent,app,mod=False):
  super().__init__(parent,text=tr('모드 UI 리소스') if mod else tr('원본 UI 리소스'));self.mod=mod;self.app=app;self.paths={};self.generation=0;self.icons=make_icons(self)
  bar=ttk.Frame(self);bar.pack(fill='x')
  ttk.Button(bar,text=tr('경로 설정'),command=app.configure_mod_paths if mod else app.configure_paths).pack(side='left');ttk.Button(bar,text=tr('새로고침'),command=self.refresh).pack(side='right')
  self.path_text=tk.StringVar();ttk.Entry(self,textvariable=self.path_text,state='readonly').pack(fill='x')
  row=ttk.Frame(self);row.pack(fill='x');self.query=tk.StringVar();entry=ttk.Entry(row,textvariable=self.query);entry.pack(side='left',fill='x',expand=True);entry.bind('<Return>',lambda e:self.search());ttk.Button(row,text=tr('검색'),command=self.search).pack(side='right')
  area=ttk.Frame(self);area.pack(fill='both',expand=True);self.tree=ttk.Treeview(area,show='tree',height=8);self.tree.pack(side='left',fill='both',expand=True)
  scroll=ttk.Scrollbar(area,command=self.tree.yview);scroll.pack(side='right',fill='y');self.tree.configure(yscrollcommand=scroll.set)
  self.tree.bind('<<TreeviewOpen>>',self.expand);self.tree.bind('<Double-Button-1>',self.open_item)
  self.notice=tk.StringVar();ttk.Label(self,textvariable=self.notice,wraplength=290).pack(fill='x');self.reload()
 def refresh(self):
  if not self.mod:self.app.template_index=None
  self.app.resource_key=None;self.app.refresh_resources();self.reload()
  if self.app.doc:self.app.draw()
 def reload(self):
  self.generation+=1;self.paths={};self.tree.delete(*self.tree.get_children());value=clean_resource_path(getattr(self.app,'mod_resource_root','') if self.mod else self.app.settings.get('resource',''));self.root_path=resource_root(value);self.path_text.set(str(self.root_path) if self.root_path else '')
  if not self.root_path or not self.root_path.is_dir():self.notice.set(tr('필수 1단계: 경로 설정에서 추출한 원본 ui 폴더를 지정하세요. 이미지와 templates를 이 폴더에서 읽습니다.'));return
  self.populate('',self.root_path);self.notice.set(tr('XML: 더블 클릭으로 가져오기 · 이미지: 미리보기'))
 def insert(self,parent,path,label=None):
  item=self.tree.insert(parent,'end',text=label or path.name,image=self.icons[file_kind(path)]);self.paths[item]=path
  if path.is_dir():self.tree.insert(item,'end',text='…')
 def populate(self,parent,path):
  try:
   for child in sorted(path.iterdir(),key=lambda p:(not p.is_dir(),p.name.casefold())):
    if child.is_dir() or child.suffix.lower() in ('.xml','.png','.jpg','.jpeg','.dds'):self.insert(parent,child)
  except OSError as e:self.notice.set(str(e))
 def expand(self,e=None):
  item=self.tree.focus();path=self.paths.get(item)
  if path and path.is_dir():
   children=self.tree.get_children(item)
   if children and children[0] not in self.paths:self.tree.delete(*children);self.populate(item,path)
 def search(self):
  query=self.query.get().strip().casefold()
  if not query:self.reload();return
  self.generation+=1;generation=self.generation;self.tree.delete(*self.tree.get_children());self.paths={}
  if not self.root_path:return
  def candidates():
   for directory,dirs,files in os.walk(self.root_path):
    for name in files:
     if Path(name).suffix.lower() in ('.xml','.png','.jpg','.jpeg','.dds'):yield Path(directory)/name
  iterator=candidates();count=0
  def step():
   nonlocal count
   if generation!=self.generation or not self.winfo_exists():return
   start=time.monotonic()
   while time.monotonic()-start<.012:
    try:path=next(iterator)
    except StopIteration:self.notice.set(trf('검색 완료 · {0}개', count));return
    relative=str(path.relative_to(self.root_path))
    if query in relative.casefold():
     self.insert('',path,relative);count+=1
     if count>=1000:self.notice.set(tr('1,000개까지 표시했습니다. 검색어를 좁혀주세요.'));return
   self.notice.set(trf('검색 중 · {0}개', count));self.after(10,step)
  step()
 def open_item(self,e=None):
  item=self.tree.identify_row(e.y) if e else self.tree.focus();path=self.paths.get(item)
  if not path or path.is_dir():return
  if path.suffix.lower()=='.xml':self.app.import_xml(path);return 'break'
  try:
   with Image.open(path) as source:im=source.convert('RGBA');im.thumbnail((400,300))
   win=tk.Toplevel(self);win.title(path.name);photo=ImageTk.PhotoImage(im);label=ttk.Label(win,image=photo);label.image=photo;label.pack(padx=8,pady=8)
   relative='ui/'+path.relative_to(self.root_path).as_posix();entry=ttk.Entry(win,width=65);entry.insert(0,relative);entry.configure(state='readonly');entry.pack(fill='x',padx=8)
   def copy_path():self.clipboard_clear();self.clipboard_append(relative)
   ttk.Button(win,text=tr('이미지 경로 복사'),command=copy_path).pack(pady=8)
  except Exception as error:messagebox.showerror(tr('미리보기'),str(error))
  return 'break'
