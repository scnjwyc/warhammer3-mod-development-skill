from i18n import tr, trf
from viewport import fit_zoom,grid_positions,zoom_origin
import tkinter as tk
from tkinter import ttk,filedialog,messagebox,simpledialog
from pathlib import Path
from usability import path_dialog
import json,math
from model import Document,Resources,LayeredResources
from project import save_project,load_project,export_zip,atomic_write

class Workspace:
 def setup_workspace(self):
  self.project_path=None;self.original_doc=None;self.session_saved=None;self.original_photos=[]
  menu=tk.Menu(self);self.configure(menu=menu)
  groups=[(tr('파일'),[(tr('새 프로젝트'),self.new_project),(tr('새 XML'),self.new_xml),(tr('XML 가져오기'),self.open),(tr('현재 XML 닫기'),self.close_document),(tr('탭 상태 저장'),self.checkpoint_tab),(tr('프로젝트 열기'),self.open_project),(tr('프로젝트 저장'),self.save_workspace),(tr('프로젝트 다른 이름으로 저장'),lambda:self.save_workspace(True)),(tr('XML 다른 이름으로 저장'),self.save),(tr('XML + 이미지 내보내기'),self.export_workspace),(tr('종료'),self.close)]),(tr('편집'),[(tr('실행 취소  Ctrl+Z'),self.undo),(tr('다시 실행  Ctrl+Y / Ctrl+Shift+Z'),self.redo)]),(tr('보기'),[(tr('화면에 맞춤'),self.fit_view),('100%',lambda:self.set_zoom(1)),(tr('선택만 보기'),self.focus_selected),(tr('전체 보기'),self.focus_all)]),(tr('설정'),[(tr('게임 / 추출 리소스 경로'),self.configure_paths),(tr('LOC TSV 불러오기'),self.load_loc),(tr('언어 / Language'),self.configure_language)]),(tr('도움말'),[(tr('0.22.2 사용 안내'),lambda:messagebox.showinfo('TWUI Studio 0.22.2',tr('Ctrl+휠: 확대·축소\nCtrl+가운데 클릭: 화면 맞춤\nCtrl+S: 프로젝트 저장\n위: 편집 / 아래: 최초 원본\n원본과 편집창은 동일 배율, 스크롤은 독립입니다.\n.pack 직접 읽기·스냅은 다음 단계입니다.')))])]
  from diagnostics_ui import show_diagnostics
  groups[-1][1].append((tr('XML 구조 검사'),lambda:show_diagnostics(self)))
  from about import show_about
  groups[-1][1].append((tr('프로그램 정보 / 이용 조건'),lambda:show_about(self)))
  for label,items in groups:
   sub=tk.Menu(menu,tearoff=False);menu.add_cascade(label=label,menu=sub)
   for text,cmd in items:sub.add_command(label=text,command=cmd)
  self.bind('<Control-Shift-Z>',lambda e:self.redo())
  self.bind('<Control-s>',lambda e:self.save_workspace())
  self.bind('<Control-Shift-S>',lambda e:self.save_workspace(True))
  for canvas in [self.canvas,self.original_canvas]:
   canvas.bind('<Control-MouseWheel>',self.zoom_wheel)
   canvas.bind('<Control-Button-4>',lambda e:self.wheel_step(1))
   canvas.bind('<Control-Button-5>',lambda e:self.wheel_step(-1))
   canvas.bind('<Control-Button-2>',lambda e:self.fit_event())

 def snapshot(self):
  if not self.doc:return None
  return {'format':'TWUIStudio','version':1,'xml':self.doc.source,'original_xml':self.original_doc.source,
   'bom':self.bom,'source_name':self.file.name,'resource_root':self.settings.get('resource',''),'mod_resource_root':getattr(self,'mod_resource_root',''),
   'loc':dict(self.loc),'preview':dict(self.preview),
   'view':{'zoom':self.zoom,'focus':self.focus_guid,'selected':self.selected,'hidden':sorted(self.hidden),'locks':sorted(self.locks),'root_lock':self.root_lock.get()}}

 def mark_saved(self):
  self.session_saved=self.snapshot()
  if hasattr(self,'title'):
   from about import VERSION
   name=Path(self.project_path).stem if self.project_path else tr('new 프로젝트')
   self.title('TWUI Studio '+VERSION+' · '+name)
 def discard_ok(self):
  if self.doc and self.snapshot()!=self.session_saved:
   return messagebox.askyesno(tr('저장하지 않은 작업'),tr('프로젝트에 저장하지 않은 변경을 버리고 계속할까요?'))
  return True
 def close(self):
  if self.discard_ok():self.destroy()

 def save_workspace(self,save_as=False):
  if not self.doc:return
  p=self.project_path if not save_as else None
  p=p or filedialog.asksaveasfilename(initialfile=self.file.stem+'.twuiproj',defaultextension='.twuiproj',filetypes=[(tr('TWUI 프로젝트'),'*.twuiproj')])
  if not p:return
  try:save_project(p,self.snapshot())
  except Exception as e:messagebox.showerror(tr('프로젝트 저장 실패'),str(e));return
  self.project_path=Path(p);self.mark_saved();self.status.set(tr('프로젝트 저장 완료: ')+str(p))

 def open_project(self):
  p=filedialog.askopenfilename(filetypes=[(tr('TWUI 프로젝트'),'*.twuiproj')])
  if not p:return
  if not self.discard_ok():return
  try:
   data=load_project(p);doc=Document(data['xml']);original=Document(data['original_xml'])
  except Exception as e:messagebox.showerror(tr('프로젝트 열기 실패'),str(e));return
  self.doc=doc;self.original_doc=original;self.file=Path(data.get('source_name') or 'untitled.twui.xml');self.bom=bool(data.get('bom',False));self.project_path=Path(p)
  self.saved_source=doc.source;self.dirty=False;self.undo_stack=[];self.redo_stack=[]
  self.hidden_images=set()
  v=data['view'];self.zoom=v.get('zoom',1);self.focus_guid=v.get('focus');self.selected=v.get('selected') if v.get('selected') in doc.by_guid else None;self.hidden=set(v.get('hidden',[]))&doc.by_guid.keys();self.preview=data.get('preview',{});self.loc=data.get('loc',{})
  self.locks=set(v.get('locks',[]))&doc.by_guid.keys();self.root_lock.set(v.get('root_lock',True))
  root=data.get('resource_root','')
  if root and Path(root).is_dir():self.settings['resource']=root
  self.refresh_resources();self.rebuild();self.mark_saved()
  if root and not Path(root).is_dir():messagebox.showinfo(tr('리소스 폴더 재연결'),tr('저장된 이미지 폴더가 없습니다. 설정에서 이 PC의 추출 리소스 폴더를 지정하세요.'))

 def configure_mod_paths(self):
  if getattr(self,'active_document',-1)<0:return
  win=tk.Toplevel(self);win.title(tr('모드 UI 리소스 경로'));win.geometry('700x220');win.transient(self);win.grab_set()
  ttk.Label(win,text=self.file.name).pack(anchor='w',padx=12,pady=8)
  ttk.Label(win,text=tr('현재 XML 탭에서만 사용할 최상위 ui 폴더를 지정하세요.\n같은 이미지 경로는 모드 폴더가 우선이며, 없으면 원본 리소스를 사용합니다.'),wraplength=660).pack(anchor='w',padx=12)
  row=ttk.Frame(win);row.pack(fill='x',padx=12,pady=12)
  value=tk.StringVar(value=getattr(self,'mod_resource_root',''));ttk.Entry(row,textvariable=value).pack(side='left',fill='x',expand=True)
  def browse():
   chosen=filedialog.askdirectory(parent=win,initialdir=value.get() or None)
   if chosen:value.set(chosen)
  ttk.Button(row,text=tr('찾기'),command=browse).pack(side='right')
  def apply():
   from model import clean_resource_path
   path=clean_resource_path(value.get())
   if path and not Path(path).is_dir():messagebox.showerror(tr('모드 UI 리소스 경로'),tr('존재하는 폴더를 지정하세요.'),parent=win);return
   self.mod_resource_root=path;self.resource_key=None;self.refresh_resources();self.mod_resource_browser.reload();self.draw();win.destroy()
  buttons=ttk.Frame(win);buttons.pack(fill='x',padx=12)
  ttk.Button(buttons,text=tr('연결 해제'),command=lambda:value.set('')).pack(side='left')
  ttk.Button(buttons,text=tr('적용'),command=apply).pack(side='right')

 def refresh_resources(self):
  BASE=Path(__file__).resolve().parent
  roots=[self.settings.get('resource',''),self.settings.get('game','')]
  # Sample resources only apply to the sample, not to arbitrary game XML.
  if self.file and self.file.name=='frame_slaves_expense.twui.xml':roots.append(str(BASE/'examples'))
  records=getattr(self,'documents',[]);active=getattr(self,'active_document',-1)
  for record in ([records[active]] if 0<=active<len(records) else []):
   payload=record['payload']
   if payload.get('source_name')=='frame_slaves_expense.twui.xml':roots.append(str(BASE/'examples'))
   path=payload.get('import_path')
   if path:
    for folder in Path(path).parents:
     if folder.name.lower()=='ui':roots.append(str(folder));break
  mod_root=getattr(self,'mod_resource_root','')
  key=(str(mod_root),tuple(str(root) for root in roots))
  if getattr(self,'resource_key',None)!=key:
   self.resources=LayeredResources(roots,mod_root);self.resource_key=key

 def export_workspace(self):
  if not self.doc:return
  rel=path_dialog(self,'ui/campaign ui/mod/'+self.file.name)
  if not rel:return
  p=filedialog.asksaveasfilename(initialfile=self.file.stem+'_export.zip',defaultextension='.zip',filetypes=[(tr('모드 리소스 ZIP'),'*.zip')])
  if not p:return
  try:r=export_zip(p,self.doc,self.resources,rel,self.bom)
  except Exception as e:messagebox.showerror(tr('내보내기 실패'),str(e));return
  if not r['written']:
   win=tk.Toplevel(self);win.title(tr('내보내기 중단 — 누락 / 잘못된 경로'));win.geometry('760x450')
   text=tk.Text(win,wrap='none');text.pack(fill='both',expand=True);text.insert('1.0',tr('리소스 경로를 연결한 뒤 다시 내보내세요.\n\n')+'\n'.join(r['missing']+r['invalid']));text.configure(state='disabled');return
  messagebox.showinfo(tr('내보내기 완료'),trf('XML과 이미지 {0}개를 원래 ui/ 경로로 묶었습니다.\n{1}\n\nZIP을 풀어 RPFM으로 가져오세요. LOC·Lua·외부 XML은 별도로 준비해야 합니다.', r['images'], p))

 def zoom_wheel(self,e):return self.wheel_step(1 if e.delta>0 else -1)
 def wheel_step(self,d):self.scale(1.15 if d>0 else 1/1.15);return 'break'
 def fit_event(self):self.fit_view();return 'break'
 def set_zoom(self,z):
  z=max(.02,min(8,z))
  if z==self.zoom:return
  box=self.boxes.get(self.selected) if self.selected and not self.is_locked(self.selected) else None
  targets=[(c,zoom_origin(c.canvasx(0),c.canvasy(0),c.winfo_width(),c.winfo_height(),self.zoom,z,box if c is self.canvas else None)) for c in (self.canvas,self.original_canvas)]
  self.zoom=z
  # Render the destination viewport, not the old viewport at the new scale.
  for c,(left,top) in targets:
   r=list(map(float,c.cget('scrollregion').split()))
   if len(r)!=4:continue
   r=[min(r[0],left-32),min(r[1],top-32),max(r[2],left+c.winfo_width()+32),max(r[3],top+c.winfo_height()+32)]
   c.configure(scrollregion=r);c.xview_moveto((left-r[0])/(r[2]-r[0]));c.yview_moveto((top-r[1])/(r[3]-r[1]))
  self.draw()
  for c,(left,top) in targets:
   r=list(map(float,c.cget('scrollregion').split()))
   if len(r)!=4:continue
   r=[min(r[0],left-32),min(r[1],top-32),max(r[2],left+c.winfo_width()+32),max(r[3],top+c.winfo_height()+32)]
   c.configure(scrollregion=r);c.xview_moveto((left-r[0])/(r[2]-r[0]));c.yview_moveto((top-r[1])/(r[3]-r[1]));self.paint_grid(c)

 def fit_tree_item(self,e):
  if self.tree.identify_region(e.x,e.y) not in ('tree','cell'):return
  if self.tree.identify_column(e.x)!='#0':return
  g=self.tree.identify_row(e.y)
  if not g:return
  self.selected=g;self.tree.selection_set(g)
  if g in getattr(self,'layout_link_rows',{}):
   from layout_links import request_import
   return request_import(self)
  self.populate()
  if g not in self.boxes:return 'break'
  self.fit_view();return 'break'
 def fit_view(self):
  if not self.doc:return
  self.update_idletasks()
  if self.selected in self.boxes:box=self.boxes[self.selected]
  else:
   boxes=[b for g,b in self.boxes.items() if self.doc.by_guid[g].get('id')!='root'] or list(self.boxes.values())
   if not boxes:return
   x=min(b[0] for b in boxes);y=min(b[1] for b in boxes)
   box=(x,y,max(b[0]+b[2] for b in boxes)-x,max(b[1]+b[3] for b in boxes)-y)
  width=self.canvas.winfo_width();height=self.canvas.winfo_height()
  info=getattr(self,'component_info',None)
  if info is not None and not info.folded:width=max(1,width-info.winfo_width()-16)
  self.zoom=fit_zoom(width,height,box);self.draw()
  x,y,w,h=box
  for c in (self.canvas,self.original_canvas):
   visible_width=width if c is self.canvas else c.winfo_width();visible_height=c.winfo_height()
   left=32+(x+w/2)*self.zoom-visible_width/2;top=32+(y+h/2)*self.zoom-visible_height/2
   region=list(map(float,c.cget('scrollregion').split()))
   if len(region)!=4:continue
   region=[min(region[0],left-32),min(region[1],top-32),max(region[2],left+c.winfo_width()+32),max(region[3],top+visible_height+32)]
   c.configure(scrollregion=region);c.xview_moveto((left-region[0])/(region[2]-region[0]));c.yview_moveto((top-region[1])/(region[3]-region[1]))
   self.paint_grid(c)
 def queue_grid(self,canvas):
  view=getattr(canvas,'image_view',None)
  if view and getattr(self,'image_view_job',None) is None:
   left,top=canvas.canvasx(0),canvas.canvasy(0)
   if left<view[0]+32 or top<view[1]+32 or left+canvas.winfo_width()>view[2]-32 or top+canvas.winfo_height()>view[3]-32:
    self.image_view_job=self.after(16,self.refresh_image_view)
  if getattr(canvas,'grid_job',None) is None:canvas.grid_job=self.after_idle(lambda:self.paint_grid(canvas))
 def refresh_image_view(self):
  self.image_view_job=None
  if self.doc:self.draw()
 def paint_grid(self,canvas):
  pending=getattr(canvas,'grid_job',None)
  if pending is not None:self.after_cancel(pending)
  canvas.grid_job=None;canvas.delete('grid')
  left,top=canvas.canvasx(0),canvas.canvasy(0);w,h=canvas.winfo_width(),canvas.winfo_height()
  for x in grid_positions(left,w,self.zoom):canvas.create_line(x,top,x,top+h,fill='#2b303a',tags=('grid',))
  for y in grid_positions(top,h,self.zoom):canvas.create_line(left,y,left+w,y,fill='#2b303a',tags=('grid',))
  canvas.tag_lower('grid')

 def draw(self):
  from rendering import ZoomImageCache
  if not hasattr(self,'zoom_images'):self.zoom_images=ZoomImageCache()
  self.zoom_images.begin()
  try:self.draw_pair()
  finally:self.zoom_images.end()
 def draw_pair(self):
  if hasattr(self,'component_info'):self.component_info.update_info(self.doc,self.selected)
  self.draw_scene()
  if self.doc is None or self.original_doc is None:return
  names=['canvas','doc','selected','photos','boxes','missing','size_cache','handle','hidden']
  saved={k:getattr(self,k,None) for k in names};status=self.status.get()
  try:
   self.canvas=self.original_canvas;self.doc=self.original_doc;self.selected=None
   # Same hidden/view filters, but immutable original XML geometry and text.
   self.draw_scene();self.original_photos=self.photos
  finally:
   for k,v in saved.items():setattr(self,k,v)
   self.status.set(status)
