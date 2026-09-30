from layout_geometry import position_offset_key
from i18n import tr, trf
from transform import TransformTools,resized,offset_delta,fixed2,alt_pressed
from component_info import ComponentInfo
import tkinter as tk
from tkinter import ttk,filedialog,messagebox,simpledialog
from pathlib import Path
import json,re,os,math
from PIL import Image,ImageTk
from model import Document,Resources,pair,number,clean_resource_path
from rendering import dimensions,raster,ZoomImageCache,visible_crop
from xml_viewer import XMLViewer
from workspace import Workspace
from multidoc import MultiDocument
from tab_history import TabHistory
from view_state import ViewActions,shown
from history_panel import HistoryPanel
from vertical_split import VerticalSplit
from usability import Usability
from split_layout import StableColumns
from viewport import stable_region,clipped_label
from inspector import ComponentInspector
import tkinter.font as tkfont
from project import atomic_write
BASE=Path(__file__).resolve().parent
CONFIG=Path(os.getenv('APPDATA',str(Path.home()))) / 'TWUIStudio' / 'settings.json'
class Studio(ViewActions,TabHistory,MultiDocument,TransformTools,Usability,Workspace,tk.Tk):
 def __init__(self):
  super().__init__();self.title('TWUI Studio 0.22.2 · '+tr('new 프로젝트'));self.geometry('1440x900');self.minsize(1000,680)
  self.doc=None;self.file=None;self.undo_stack=[];self.redo_stack=[];self.selected=None;self.focus_guid=None;self.zoom=1.;self.photos=[];self.boxes={};self.hidden=set();self.hidden_images=set();self.preview={};self.dirty=False
  try:self.settings=json.loads(CONFIG.read_text('utf-8'))
  except (OSError,ValueError):self.settings={}
  self.resources=Resources([self.settings.get('resource',''),self.settings.get('game',''),str(BASE/'examples')])
  self.style=ttk.Style(self);self.style.theme_use('clam')
  toolbar=ttk.Frame(self,padding=8);toolbar.pack(fill='x')
  for text,cmd in [(tr('XML 가져오기'),self.open),(tr('다른 이름으로 저장'),self.save),(tr('설정'),self.configure_paths),(tr('실행 취소'),self.undo),(tr('다시 실행'),self.redo),(tr('샘플 열기'),lambda:self.open(BASE/'examples/frame_slaves_expense.twui.xml'))]:ttk.Button(toolbar,text=text,command=cmd).pack(side='left',padx=3)
  self.status=tk.StringVar(value=tr('XML을 열거나 샘플 열기를 선택하세요.'));ttk.Label(self,textvariable=self.status,padding=6).pack(side='bottom',fill='x')
  split=StableColumns(self);split.pack(fill='both',expand=True)
  left_split=VerticalSplit(split);split.add(left_split,weight=0);left=ttk.Frame(left_split,padding=8);left_split.add(left);self.left_split=left_split
  ttk.Label(left,text=tr('구성 요소'),font=('',13,'bold')).pack(anchor='w')
  self.tree_query=tk.StringVar();search=ttk.Frame(left);search.pack(fill='x');ttk.Entry(search,textvariable=self.tree_query).pack(side='left',fill='x',expand=True);ttk.Button(search,text='⌄',width=3,command=lambda:self.expand_tree(True)).pack(side='right');self.tree_query.trace_add('write',lambda *a:self.rebuild() if self.doc and not getattr(self,"switching",False) else None)
  treearea=ttk.Frame(left);treearea.pack(fill='both',expand=True);treearea.rowconfigure(0,weight=1);treearea.columnconfigure(0,weight=1)
  self.tree=ttk.Treeview(treearea,show='tree',height=6,selectmode='extended');self.tree.grid(row=0,column=0,sticky='nsew')
  treesb=ttk.Scrollbar(treearea,command=self.tree.yview);treesb.grid(row=0,column=1,sticky='ns')
  def tree_scroll(first,last):
   treesb.set(first,last)
   if float(first)<=0 and float(last)>=1:treesb.grid_remove()
   else:treesb.grid()
  self.tree.configure(yscrollcommand=tree_scroll);self.tree.bind('<<TreeviewSelect>>',self.select_tree)
  search.pack_forget();search.pack(fill='x')
  ttk.Button(search,text='⌃',width=3,command=lambda:self.expand_tree(False)).pack(side='right')
  buttons=ttk.Frame(left);buttons.pack(fill='x')
  for col in range(3):buttons.columnconfigure(col,weight=1,uniform='component_buttons')
  for index,(text,cmd) in enumerate([(tr('표시/숨김'),self.toggle_hidden),(tr('선택만 보기'),self.focus_selected),(tr('전체 보기'),self.focus_all),(tr('대상 잠금'),lambda:self.lock_action('lock')),(tr('대상 잠금 해제'),lambda:self.lock_action('unlock')),(tr('모든 잠금 해제'),lambda:self.lock_action('all_unlock'))]):
   ttk.Button(buttons,text=text,command=cmd,width=1).grid(row=index//3,column=index%3,sticky='ew')
  self.fields={}
  self.fields={key:tk.StringVar() for key in ('x','y','width','height','imagepath','text','textlabel')}
  self.detail=tk.Text(left,height=6,width=38,wrap='word',font=('',9));self.detail.pack(fill='x')
  right=ttk.Frame(split,width=650);split.add(right,weight=1)
  self.xml_viewer=XMLViewer(split, format_command=self.format_xml);split.add(self.xml_viewer,weight=0)
  self.after(100,lambda: (split.sashpos(0,300),split.sashpos(1,max(650,self.winfo_width()-440))))
  compare=ttk.Panedwindow(right,orient='vertical');compare.pack(fill='both',expand=True)
  editor=ttk.Frame(compare);compare.add(editor,weight=3)
  original=ttk.Frame(compare);compare.add(original,weight=2)
  self.after(120,lambda:compare.sashpos(0,max(250,int(compare.winfo_height()*.6))))
  bar=ttk.Frame(editor,padding=5);bar.pack(fill='x');ttk.Label(bar,text=tr('UI 편집창 · Ctrl+휠 확대 / Ctrl+가운데 클릭 맞춤')).pack(side='left')
  for text,cmd in [('−',lambda:self.scale(.8)),('+',lambda:self.scale(1.25))]:ttk.Button(bar,text=text,width=3,command=cmd).pack(side='right')
  area=ttk.Frame(editor);area.pack(fill='both',expand=True);area.rowconfigure(0,weight=1);area.columnconfigure(0,weight=1)
  self.canvas=tk.Canvas(area,bg='#242831',highlightthickness=0);self.canvas.grid(row=0,column=0,sticky='nsew');self.component_info=ComponentInfo(self.canvas)
  sx=ttk.Scrollbar(area,orient='horizontal',command=self.canvas.xview);sx.grid(row=1,column=0,sticky='ew')
  sy=ttk.Scrollbar(area,orient='vertical',command=self.canvas.yview);sy.grid(row=0,column=1,sticky='ns');self.canvas.configure(xscrollcommand=sx.set,yscrollcommand=sy.set)
  ttk.Label(original,text=tr('원본 UI · 처음 불러온 XML / 읽기 전용'),padding=5).pack(fill='x')
  oa=ttk.Frame(original);oa.pack(fill='both',expand=True);oa.columnconfigure(0,weight=1);oa.rowconfigure(0,weight=1)
  self.original_canvas=tk.Canvas(oa,bg='#242831',highlightthickness=0);self.original_canvas.grid(row=0,column=0,sticky='nsew')
  ox=ttk.Scrollbar(oa,orient='horizontal',command=self.original_canvas.xview);ox.grid(row=1,column=0,sticky='ew')
  oy=ttk.Scrollbar(oa,orient='vertical',command=self.original_canvas.yview);oy.grid(row=0,column=1,sticky='ns');self.original_canvas.configure(xscrollcommand=ox.set,yscrollcommand=oy.set)
  self.history_panel=HistoryPanel(oa,self)
  for cv,hbar,vbar in ((self.canvas,sx,sy),(self.original_canvas,ox,oy)):
   cv.configure(xscrollcommand=lambda first,last,c=cv,bar=hbar:(bar.set(first,last),self.queue_grid(c)),yscrollcommand=lambda first,last,c=cv,bar=vbar:(bar.set(first,last),self.queue_grid(c)))
   cv.bind('<Configure>',lambda e,c=cv:self.queue_grid(c),add='+')
  self.tree.bind('<Double-Button-1>',self.fit_tree_item)
  self.canvas.bind('<ButtonPress-1>',self.press);self.canvas.bind('<B1-Motion>',self.motion);self.canvas.bind('<ButtonRelease-1>',self.release)
  self.bind('<Control-o>',lambda e:self.open());self.bind('<Control-s>',lambda e:self.save());self.bind('<Control-z>',lambda e:self.undo());self.bind('<Control-y>',lambda e:self.redo())
  self.protocol('WM_DELETE_WINDOW',self.close);self.loc={};self.setup_workspace();self.setup_usability();self.canvas.bind('<Double-Button-1>',self.open_inspector);self.canvas.bind('<Escape>',self.deselect);self.canvas.bind('<Motion>',self.transform_hover);self.detail.pack_forget();self.setup_multi(left,right,compare)
 def configure_paths(self):
  win=tk.Toplevel(self);win.title(tr('경로 설정'));win.geometry('820x500');win.minsize(620,440);values={}
  ttk.Label(win,text=tr('필수 1단계 · 원본 UI 폴더 설정'),padding=8).pack(anchor='w')
  ttk.Checkbutton(win,text=tr('root 고정 (자식 요소는 계속 편집 가능)'),variable=self.root_lock,command=self.tree_states).pack(anchor='w',padx=12,pady=6)
  for key,label in [('game',tr('게임 설치 폴더')),('resource',tr('추출 리소스 폴더'))]:
   row=ttk.Frame(win,padding=8);row.pack(fill='x');ttk.Label(row,text=label,width=20).pack(side='left');v=tk.StringVar(value=self.settings.get(key,''));values[key]=v;ttk.Entry(row,textvariable=v).pack(side='left',fill='x',expand=True)
   def browse(v=v):
    p=filedialog.askdirectory(parent=win)
    if p:v.set(p)
   ttk.Button(row,text=tr('찾기'),command=browse).pack(side='right')
  note=ttk.Label(win,text=tr('현재 버전에서는 추출 리소스 폴더가 필요합니다. 게임 설치 경로만 지정해도 .pack 내부의 이미지나 XML을 불러올 수는 없습니다.\n\nRPFM 또는 AssetEditor로 게임의 ui 폴더 전체를 추출한 뒤, 가장 상위의 ui 폴더를 선택하세요. 예: D:/ModData/ui\n선택한 폴더 아래에 skins, campaign ui, battle ui 등의 하위 폴더가 있어야 합니다.\n\nXML의 ui/skins/... 경로는 이 ui 폴더를 기준으로 찾습니다.'),padding=12,justify='left',wraplength=780);note.pack(fill='x')
  win.bind('<Configure>',lambda e:note.configure(wraplength=max(300,win.winfo_width()-40)) if e.widget is win else None)
  def done():
   candidate={k:clean_resource_path(v.get()) for k,v in values.items()}
   for key,path in candidate.items():
    if path and not Path(path).is_dir():messagebox.showerror(tr('경로 확인'),tr('폴더가 없습니다: ')+path);return
   self.settings={**self.settings,**candidate,'root_lock':self.root_lock.get()}
   try:CONFIG.parent.mkdir(parents=True,exist_ok=True);CONFIG.write_text(json.dumps(self.settings,ensure_ascii=False),'utf-8')
   except OSError as e:messagebox.showerror(tr('설정 저장 실패'),str(e));return
   self.resource_key=None;self.refresh_resources();win.destroy();self.draw()
   if hasattr(self,"resource_browser"):self.resource_browser.reload()
  ttk.Label(win,text=tr('templates 하위 폴더가 있으면 상태 원본을 자동으로 참조합니다. 원본 파일은 수정하지 않습니다. DLC 자료 추가 후 원본 UI 리소스의 새로고침을 누르세요.'),wraplength=760,padding=8).pack(fill='x')
  actions=ttk.Frame(win);actions.pack(pady=4)
  ttk.Button(actions,text=tr('저장'),command=done).pack(side='left',padx=4)
  ttk.Button(actions,text=tr('언어 / Language'),command=self.configure_language).pack(side='left',padx=4)
 def configure_language(self):
  win=tk.Toplevel(self);win.title(tr('언어 / Language'));win.transient(self);win.geometry('520x210');win.minsize(460,200)
  ttk.Label(win,text=tr('프로그램 언어'),padding=12).pack(anchor='w')
  choice=ttk.Combobox(win,state='readonly',values=[tr('한국어'),'English']);choice.pack(fill='x',padx=12);choice.current(1 if self.settings.get('language','ko')=='en' else 0)
  ttk.Label(win,text=tr('언어는 다음 실행부터 적용됩니다. 작업을 저장한 뒤 프로그램을 다시 시작하세요.'),wraplength=470,padding=12).pack(fill='x')
  def save_language():
   settings={**self.settings,'language':'en' if choice.current()==1 else 'ko'}
   try:CONFIG.parent.mkdir(parents=True,exist_ok=True);CONFIG.write_text(json.dumps(settings,ensure_ascii=False),'utf-8')
   except OSError as e:messagebox.showerror(tr('설정 저장 실패'),str(e),parent=win);return
   self.settings=settings;win.destroy()
  ttk.Button(win,text=tr('저장'),command=save_language).pack(pady=6)
 def open(self,path=None):self.import_xml(path)
 def rebuild(self):
  from diagnostics_ui import install_tree_warnings
  from diagnostics import highest_severity, marker_kind
  install_tree_warnings(self)
  if self.selected not in self.doc.by_guid:self.selected=None
  if isinstance(self.focus_guid,list):self.focus_guid=[g for g in self.focus_guid if g in self.doc.by_guid]
  elif self.focus_guid not in self.doc.by_guid:self.focus_guid=None
  selections=list(self.tree.selection())
  if hasattr(self,'tabs') and self.active_document>=0:self.tabs.tab(self.active_document,text=self.file.name+(' *' if self.dirty else ''))
  self.xml_viewer.set_document(self.doc)
  expanded={g for g in self.doc.by_guid if self.tree.exists(g) and self.tree.item(g,'open')}
  query=self.tree_query.get().strip().casefold();allowed=set()
  if query:
   for g,c in self.doc.by_guid.items():
    if query in c.get('id','').casefold():
     while g and g not in allowed:allowed.add(g);g=self.doc.parents.get(g)
  self.tree.delete(*self.tree.get_children())
  def add(n,parent=''):
   g=n.get('this')
   if not g or (query and g not in allowed):return
   c=self.doc.by_guid.get(g)
   if c is None:return
   self.tree.insert(parent,'end',iid=g,text=c.get('id',n.tag),image=self.diagnostic_icons.get(marker_kind(self.doc.issues_by_key.get(g,[])),''),open=bool(query) or g in expanded or parent=='')
   for ch in n.children:add(ch,g)
  from hierarchy_edit import NO_PARENT
  for n in self.doc.hierarchy.children:
   if n.get('this') not in self.doc.unlinked_keys:add(n)
  self.tree.insert('','end',iid=NO_PARENT,text='no parent',open=True)
  for n in self.doc.hierarchy.children:
   if n.get('this') in self.doc.unlinked_keys:add(n,NO_PARENT)
  if self.selected in self.doc.by_guid and self.tree.exists(self.selected):self.tree.selection_set([g for g in selections if self.tree.exists(g)] or [self.selected]);self.populate()
  from layout_links import decorate_tree
  decorate_tree(self)
  self.tree_states();self.draw()
 def format_xml(self):
  if not self.doc:return
  from xml_format import format_xml
  try:
   source=format_xml(self.doc.source)
   if source!=self.doc.source:self.commit(source,tr('XML 정렬'))
  except ValueError as error:messagebox.showerror(tr('속성 확인'),str(error),parent=self)

 def commit(self,source,label=None):
  if source==self.doc.source:return
  try:d=Document(source)
  except Exception as e:messagebox.showerror(tr('변경 실패'),str(e));return
  self.cut_pending=None
  before=self.action_state();self.doc=d;self.record_action(before,label);self.dirty=source!=self.saved_source;self.rebuild()
 def undo(self):return self.history_travel()
 def redo(self):return self.history_travel(True)
 def save(self):
  if not self.doc:return
  p=filedialog.asksaveasfilename(initialfile=self.file.stem+'_edited.xml',defaultextension='.xml',filetypes=[('XML','*.xml')])
  if not p:return
  try:
   atomic_write(p,(b'\xef\xbb\xbf' if self.bom else b'')+self.doc.source.encode('utf-8'));self.saved_source=self.doc.source;self.dirty=False;self.status.set(tr('저장 완료: ')+p);self.tabs.tab(self.active_document,text=self.file.name)
  except OSError as e:messagebox.showerror(tr('저장 실패'),str(e))
 def select_tree(self,e=None):
  sel=self.tree.selection()
  if sel and sel[0]!=self.selected:self.selected=sel[0];self.populate();self.refresh_selection()
 def selected_parts(self):
  c=self.doc.by_guid[self.selected];s=self.doc.state(c);ims=c.child('componentimages');return c,s,ims.children[0] if ims is not None and ims.children else None,s.child('component_text') if s else None
 def populate(self):
  if self.selected not in self.doc.by_guid:return
  c,s,im,t=self.selected_parts();self.xml_viewer.reveal(c);x,y=pair(c.get(position_offset_key(c)))
  for k,v in dict(x=x,y=y,width=s.get('width','') if s else '',height=s.get('height','') if s else '',imagepath=im.get('imagepath','') if im else '',text=t.get('text','') if t else '',textlabel=t.get('textlabel','') if t else '').items():self.fields[k].set(v)
  parent=self.doc.by_guid.get(self.doc.parents.get(self.selected));auto=parent is not None and parent.child('LayoutEngine') is not None
  self.detail.delete('1.0','end');self.detail.insert('end',trf('ID: {0}\n상태: {1}\n배치: {2} / 부모 목록: {3}\n이미지 속성은 첫 이미지 기준입니다.\nCCO·Lua 실행 및 종족 스킨 치환은 미지원.', c.get('id'), s.get('name') if s else tr('없음'), c.get('docking', tr('좌표')), auto))
 def apply(self):
  if not self.selected:return
  if self.is_locked(self.selected):messagebox.showinfo(tr('요소 잠금'),tr('잠긴 요소입니다. 우클릭 메뉴에서 잠금을 해제하세요.'));return
  c,s,im,t=self.selected_parts();v={k:x.get() for k,x in self.fields.items()}
  try:
   for k in ['x','y','width','height']:
    if v[k] and not math.isfinite(float(v[k])):raise ValueError()
   if any(v[k] and float(v[k])<0 for k in ['width','height']):raise ValueError()
  except ValueError:messagebox.showerror(tr('입력 확인'),tr('좌표와 크기는 숫자, 크기는 0 이상이어야 합니다.'));return
  position_key=position_offset_key(c)
  position=f"{v['x'] or 0},{v['y'] or 0}"
  changes=[(c,{position_key:position})] if pair(position)!=pair(c.get(position_key)) else []
  if s:
   changes.append((s,{k:v[k] for k in ['width','height'] if v[k] and v[k]!=s.get(k,'')}))
   metrics=s.child('imagemetrics')
   if metrics:
    for m in metrics.children:
     delta={}
     for key in ['width','height']:
      if v[key] and s.get(key) and m.get(key) and m.get('canresize'+key,'true')!='false':
       difference=number(v[key])-number(s.get(key))
       if difference:delta[key]=str(max(1,number(m.get(key))+difference))
     if delta:changes.append((m,delta))
  if im and v['imagepath']!=im.get('imagepath',''):changes.append((im,{'imagepath':v['imagepath']}))
  if t:changes.append((t,{k:v[k] for k in ['text','textlabel'] if v[k]!=t.get(k,'')}))
  self.commit(self.doc.patch(changes))
 def load_loc(self):
  p=filedialog.askopenfilename(filetypes=[(tr('LOC 내보내기 TSV'),'*.tsv *.txt')])
  if not p:return
  try:
   b=Path(p).read_bytes();text=b.decode('utf-16' if b.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
   self.loc={a[0]:a[1] for line in text.splitlines() if len(a:=line.split('\t'))>=2};self.draw()
  except Exception as e:messagebox.showerror(tr('TSV 읽기 실패'),str(e))
 def focus_selected(self):self.view_action('only')
 def focus_all(self):self.view_action('all_show')
 def toggle_hidden(self):self.view_action('toggle')
 def scale(self,f):self.set_zoom(self.zoom*f)
 def draw_scene(self):
  view_left,view_top=self.canvas.canvasx(0),self.canvas.canvasy(0)
  old_region=tuple(map(float,self.canvas.cget('scrollregion').split()))
  image_view=(view_left-128,view_top-128,view_left+self.canvas.winfo_width()+128,view_top+self.canvas.winfo_height()+128)
  self.canvas.image_view=image_view
  self.canvas.delete('all');self.photos=[];self.boxes={};self.missing=set();self.size_cache={}
  if not self.doc:return
  self.paint_grid(self.canvas)
  roots=[n.get('this') for n in self.doc.hierarchy.children]
  def visit(g,px,py,pw,ph,forced=None,top=False):
   c=self.doc.by_guid.get(g)
   if c is None:return (0,0)
   s=self.doc.state(c);w,h=dimensions(self.doc,g,set(),self.size_cache)
   from layout_geometry import component_position
   x,y=component_position(c,(w,h),(pw,ph))
   if forced is not None:x,y=forced
   if top:x=y=0
   x+=px;y+=py;visible=shown(self.doc,g,self.hidden,self.focus_guid)
   if visible:self.boxes[g]=(x,y,w,h)
   z=self.zoom;ox=32+x*z;oy=32+y*z
   if s and visible:
    ims=c.child('componentimages');lookup={i.get('this'):i.get('imagepath','') for i in ims.children} if ims is not None else {};metrics=s.child('imagemetrics')
    if metrics:
     for m in metrics.children:
      if self.canvas is not self.original_canvas and (g,m.get('componentimage')) in getattr(self,'hidden_images',set()):continue
      path=lookup.get(m.get('componentimage'),'');asset=self.resources.resolve(path) if path else None
      iw=number(m.get('width'),w);ih=number(m.get('height'),h);ix,iy=pair(m.get('offset'))
      # Apply size deltas to resizable image layers, retaining fixed borders.
      if s.get('width') and m.get('canresizewidth','true')!='false':iw+=w-number(s.get('width'))
      if s.get('height') and m.get('canresizeheight','true')!='false':ih+=h-number(s.get('height'))
      dockpoint=m.get('dockpoint','').replace('_',' ').title()
      if dockpoint:
       ix=(w-iw if 'Right' in dockpoint else (w-iw)/2 if 'Center' in dockpoint else 0)
       iy=(h-ih if 'Bottom' in dockpoint else (h-ih)/2 if dockpoint.startswith('Center') else 0)
       dx,dy=pair(m.get('dock_offset'));ix+=dx;iy+=dy
      if asset and iw>0 and ih>0:
       try:
        size=(max(1,min(4096,round(iw*z))),max(1,min(4096,round(ih*z))))
        if not hasattr(self,'zoom_images'):self.zoom_images=ZoomImageCache()
        image_x,image_y=ox+ix*z,oy+iy*z
        self.canvas.create_rectangle(image_x,image_y,image_x+size[0],image_y+size[1],outline='',width=0,tags=('image_extent',))
        crop=visible_crop(image_x,image_y,size,image_view)
        if crop is not None:
         photo=self.zoom_images.photo(asset,iw,ih,m,size,self.canvas,crop=crop);self.photos.append(photo)
         self.canvas.create_image(image_x+crop[0],image_y+crop[1],image=photo,anchor='nw')
       except Exception:self.missing.add(path)
      elif path:self.missing.add(path);self.canvas.create_rectangle(ox+ix*z,oy+iy*z,ox+(ix+iw)*z,oy+(iy+ih)*z,outline='#bb8160',dash=(3,3))
    t=s.child('component_text')
    if t:
     text=self.preview.get(g,self.loc.get('uied_component_texts_localised_string_'+t.get('textlabel',''),t.get('text','')));text=re.sub(r'\[\[.*?\]\]','',text)
     tx,ty=pair(t.get('textyoffset'));center=t.get('texthalign')=='Center';color=t.get('font_m_colour','#FFF8D7FF')[:7]
     self.canvas.create_text(ox+(w/2 if center else 0)*z+tx*z,oy+ty*z+(h/2 if t.get('textvalign')=='Center' else 0)*z,text=text,fill=color,anchor='center' if t.get('textvalign')=='Center' and center else 'w' if t.get('textvalign')=='Center' else 'n' if center else 'nw',font=('Arial',max(6,round(number(t.get('font_m_size'),12)*z))))
   if visible and c.get('id')!='root':self.canvas.create_rectangle(ox,oy,ox+w*z,oy+h*z,outline='#515d70',tags=('bounds',))
   layout=c.child('LayoutEngine');children=self.doc.children.get(g,[]);positions={}
   if layout is not None:
    from layout_geometry import list_positions
    sizes={child:dimensions(self.doc,child,set(),self.size_cache) for child in children}
    positions,_=list_positions(layout,children,sizes,(w,h))
   for child in children:visit(child,x,y,w,h,positions.get(child))
   return w,h
  for g in roots:visit(g,0,0,1600,900,top=True)
  items=[i for i in self.canvas.find_all() if 'grid' not in self.canvas.gettags(i)]
  bbox=self.canvas.bbox(*items) if items else None
  region=stable_region(old_region,bbox,view_left,view_top,self.canvas.winfo_width(),self.canvas.winfo_height())
  self.canvas.configure(scrollregion=region)
  self.canvas.xview_moveto((view_left-region[0])/(region[2]-region[0]));self.canvas.yview_moveto((view_top-region[1])/(region[3]-region[1]))
  Studio.paint_selection(self)
  self.status.set(trf('{0} {1} · {2} 요소 · {3:.0%} · 누락 이미지 {4} · 근사 미리보기 (스킨·CCO 미실행 / 목록·9분할 해석 검증 중)', self.file.name, tr('● 변경됨') if self.dirty else '', len(self.doc.components), self.zoom, len(self.missing)))
 def refresh_selection(self):
  if hasattr(self,'component_info'):self.component_info.update_info(self.doc,self.selected)
  self.paint_selection()
 def paint_selection(self):
  self.canvas.delete('selection_overlay')
  before=set(self.canvas.find_all())
  if self.selected in self.boxes and not self.is_locked(self.selected):
   x,y,w,h=self.boxes[self.selected];z=self.zoom;a,b=32+x*z,32+y*z;c,d=a+w*z,b+h*z;self.paint_transform(a,b,c,d)
   font=tkfont.Font(family='Arial',size=9);self.label_font=font;limit=max(0,w*z*.9-8)
   label=clipped_label(self.doc.by_guid[self.selected].get('id',''),font.measure,limit)
   if label:
    tw=font.measure(label)+8;th=font.metrics('linespace')+4
    self.canvas.create_rectangle(a,b-th-2,a+tw,b-2,fill='#294856',outline='',tags=('selection_label',))
    self.canvas.create_text(a+4,b-th,anchor='nw',text=label,font=font,fill='#d9f1fa',tags=('selection_label',))
  for item in set(self.canvas.find_all())-before:self.canvas.addtag_withtag('selection_overlay',item)
 def open_inspector(self,e=None):
  self.drag=None
  if len(self.selected_guids())>1:return 'break'
  if e is not None and self.is_locked(self.selected):return 'break'
  if self.doc and self.selected in self.doc.by_guid:
   if self.selected in self.doc.placeholder_keys:
    messagebox.showinfo(tr('XML 구조 검사'),tr('정의가 없는 임시 항목은 XML 구조 검사에서 연결을 먼저 확인하세요.'));return 'break'
   ComponentInspector(self)
  return 'break'
 def deselect(self,e=None):
  self.selected=None;self.drag=None;self.tree.selection_remove(*self.tree.selection());self.canvas.delete('dragghost');self.refresh_selection();return 'break'
 def expand_tree(self,opened):
  if self.doc:
   for g in self.doc.by_guid:
    if self.tree.exists(g):self.tree.item(g,open=opened)
 def reveal_tree(self,g):
  if not self.tree.exists(g):
   self.tree_query.set('');self.rebuild()
  if not self.tree.exists(g):return
  parent=self.tree.parent(g)
  while parent:self.tree.item(parent,open=True);parent=self.tree.parent(parent)
  self.tree.selection_set(g);self.tree.see(g)
 def press(self,e):
  self.canvas.focus_set()
  if e.state & 4:return
  handle=None if self.is_locked(self.selected) else self.handle_at(e)
  e.x=self.canvas.canvasx(e.x);e.y=self.canvas.canvasy(e.y)
  if not self.doc:return
  resize=handle is not None and handle!=(1,1)
  if handle is None:
   target=self.canvas_target(e.x,e.y)
   if target is None:self.deselect();return
   self.selected=target;self.reveal_tree(target);self.populate();self.refresh_selection()
  if self.is_locked(self.selected):self.drag=None;return
  self.shift_move=bool(e.state & 1) and not resize;self.move_axis=None;self.move_delta=(0.,0.)
  self.drag_moved=False;self.copy_drag=not resize and alt_pressed(e.state,self.tk.call("tk","windowingsystem"))
  if self.selected in self.boxes:
   self.transform_handle=handle if resize else (1,1);self.transform_box=self.boxes[self.selected]
   self.drag=(e.x,e.y,resize,{k:v.get() for k,v in self.fields.items()})
 def motion(self,e):
  e.x=self.canvas.canvasx(e.x);e.y=self.canvas.canvasy(e.y)
  if not getattr(self,'drag',None):return
  x,y,resize,v=self.drag
  if abs(e.x-x)+abs(e.y-y)<3:return
  self.drag_moved=True
  dx=(e.x-x)/self.zoom;dy=(e.y-y)/self.zoom
  if not resize and (self.shift_move or e.state & 1):
   self.shift_move=True
   if self.move_axis is None:self.move_axis='x' if abs(dx)>=abs(dy) else 'y'
   if self.move_axis=='x':dy=0.
   else:dx=0.
   self.move_delta=(dx,dy)
  node=self.doc.by_guid[self.selected];before=self.transform_box
  after=resized(before,self.transform_handle,dx,dy,alt=alt_pressed(e.state,self.tk.call('tk','windowingsystem')),shift=bool(e.state & 1),allow_x=node.get('allowhorizontalresize')!='false',allow_y=node.get('allowverticalresize')!='false')
  ox,oy=offset_delta(node,before,after)
  self.fields['x'].set(fixed2(number(v['x'])+ox));self.fields['y'].set(fixed2(number(v['y'])+oy))
  self.fields['width'].set(fixed2(number(v['width'])+after[2]-before[2]));self.fields['height'].set(fixed2(number(v['height'])+after[3]-before[3]))
  self.canvas.delete('dragghost');bx,by,bw,bh=after;z=self.zoom
  self.canvas.create_rectangle(32+bx*z,32+by*z,32+(bx+bw)*z,32+(by+bh)*z,outline='#fff',dash=(4,3),tags='dragghost')
 def release(self,e):
  e.x=self.canvas.canvasx(e.x);e.y=self.canvas.canvasy(e.y)
  if not getattr(self,'drag',None):return
  x,y,resize,v=self.drag;self.drag=None
  if not getattr(self,'drag_moved',False):return
  if getattr(self,'copy_drag',False):
   self.canvas.delete('dragghost');self.alt_duplicate(self.fields['x'].get(),self.fields['y'].get());return
  if getattr(self,'shift_move',False) and not resize:
   node=self.doc.by_guid[self.selected];ox,oy=pair(node.get('offset'));dx,dy=self.move_delta
   self.canvas.delete('dragghost');self.commit(self.doc.patch([(node,{'offset':f'{fixed2(ox+dx)},{fixed2(oy+dy)}'})]),tr('축 제한 위치 이동'));return
  parent=self.doc.by_guid.get(self.doc.parents.get(self.selected))
  if parent is not None and parent.child('LayoutEngine') is not None:
   self.populate();self.draw();messagebox.showinfo(tr('목록 배치'),tr('부모 목록이 배치를 결정하는 요소입니다. 속성 창에서 크기와 목록 설정을 조정하세요.'));return
  self.canvas.delete('dragghost');self.apply()
if __name__=='__main__':Studio().mainloop()
