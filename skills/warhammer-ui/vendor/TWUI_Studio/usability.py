from i18n import tr, trf
import tkinter as tk
from tkinter import ttk
from tree_columns import fit_columns,move_divider
from view_state import shown,descendants,top_targets

def path_dialog(parent,initial):
 win=tk.Toplevel(parent);win.title(tr('XML 게임 내 경로'));win.geometry('860x180');win.minsize(540,160);win.transient(parent)
 win.columnconfigure(0,weight=1);win.rowconfigure(1,weight=1)
 ttk.Label(win,text=tr('내보낼 XML의 게임 내 상대 경로 (ui/로 시작)'),padding=12).grid(row=0,column=0,sticky='w')
 value=tk.StringVar(value=initial);entry=ttk.Entry(win,textvariable=value);entry.grid(row=1,column=0,sticky='ew',padx=12)
 buttons=ttk.Frame(win,padding=12);buttons.grid(row=2,column=0,sticky='e');result=[]
 def done():result.append(value.get().strip());win.destroy()
 ttk.Button(buttons,text=tr('다음'),command=done).pack(side='left',padx=4);ttk.Button(buttons,text=tr('취소'),command=win.destroy).pack(side='left')
 win.bind('<Return>',lambda e:done());win.bind('<Escape>',lambda e:win.destroy());entry.focus_set();entry.selection_range(0,'end');win.grab_set();parent.wait_window(win)
 return result[0] if result else None

def visibility(doc,g,hidden):
 if g in hidden:return tr('숨김')
 p=doc.parents.get(g)
 while p:
  if p in hidden:return tr('부모 숨김')
  p=doc.parents.get(p)
 return tr('표시')

class Usability:
 def setup_usability(self):
  ttk.Style(self).configure('Components.Treeview',indent=10);self.tree.configure(style='Components.Treeview')
  self.locks=set();self.root_lock=tk.BooleanVar(value=self.settings.get('root_lock',True))
  self.tree.configure(columns=('visibility','locked'),show='tree headings')
  self.tree.heading('#0',text=tr('구성 요소'));self.tree.column('#0',width=145,minwidth=80,stretch=False)
  for key,label,w in [('visibility',tr('보기'),65),('locked',tr('잠금'),48)]:
   self.tree.heading(key,text=label);self.tree.column(key,width=w,minwidth=36,stretch=False)
  for key,width in self.settings.get('tree_column_widths',{}).items():
   if key in ('#0','visibility','locked') and isinstance(width,int):self.tree.column(key,width=max(24,width))
  self.tree.bind('<ButtonPress-1>',self.column_press,add='+')
  self.tree.bind('<ButtonRelease-1>',self.column_release,add='+')
  self.tree.bind('<B1-Motion>',self.column_motion,add='+')
  self.tree.bind('<Configure>',self.column_configure,add='+')
  self.column_drag=None;self.column_job=None
  self.after_idle(self.fit_tree_columns)
  self.tree.tag_configure('hidden',foreground='#929292')
  self.tree.bind('<Button-3>',self.lock_menu)
  self.canvas.bind('<Button-3>',self.lock_menu)
  for c in (self.canvas,self.original_canvas):
   c.bind('<ButtonPress-2>',self.pan_start);c.bind('<B2-Motion>',self.pan_move);c.bind('<ButtonRelease-2>',lambda e:e.widget.configure(cursor=''))
 def is_locked(self,g):
  return g in getattr(self.doc,'placeholder_keys',set()) or g in self.locks or (self.root_lock.get() and self.doc and g in self.doc.by_guid and self.doc.by_guid[g].get('id')=='root')
 def tree_states(self):
  self.tree.tag_configure('cut_pending',foreground='#999999')
  if not self.doc:return
  for g in self.doc.by_guid:
   if self.tree.exists(g):
    state=self.display_visibility(g);self.tree.item(g,values=(state,tr('잠금') if self.is_locked(g) else ''),tags=('cut_pending',) if getattr(self,'cut_pending',None) and self.cut_pending[0]==self.doc.source and g==self.cut_pending[1] else ('hidden',) if state!=tr('표시') else ())
 def canvas_target(self,x,y):
  for g,(bx,by,w,h) in reversed(list(self.boxes.items())):
   if not self.is_locked(g) and 32+bx*self.zoom<=x<=32+(bx+w)*self.zoom and 32+by*self.zoom<=y<=32+(by+h)*self.zoom:return g
  return None
 def lock_action(self,action):
  before=self.action_state() if hasattr(self,'action_state') else None
  targets=self.selected_guids(expand_groups=True) if hasattr(self,'selected_guids') else [self.selected]
  targets=[g for g in targets if g in self.doc.by_guid]
  if not targets and action not in ('all_unlock','all_lock'):return
  if action=='all_unlock':self.locks.clear();self.root_lock.set(False)
  elif action=='all_lock':self.locks=set(self.doc.by_guid)
  elif action=='others':
   self.locks=set(self.doc.by_guid)-set(targets)
   if any(self.doc.by_guid[g].get('id')=='root' for g in targets):self.root_lock.set(False)
  elif action=='parent':self.locks.update(p for g in targets if (p:=self.doc.parents.get(g)) and p not in targets)
  elif action=='children':self.locks.update((descendants(self.doc,targets)-set(targets)) | (self.selected_group_members() if hasattr(self,'selected_group_members') else set()))
  else:
   unlock=action=='unlock' or (action=='toggle' and all(self.is_locked(g) for g in targets))
   for g in targets:
    if unlock:
     self.locks.discard(g)
     if self.doc.by_guid[g].get('id')=='root':self.root_lock.set(False)
    else:self.locks.add(g)
  if before is not None:self.record_action(before)
  self.tree_states();self.drag=None;self.draw()
 def display_visibility(self,g):
  return tr('표시') if shown(self.doc,g,self.hidden,getattr(self,'focus_guid',None)) else tr('숨김')
 def toggle_lock(self):self.lock_action('toggle')
 def lock_menu(self,e):
  if e.widget==self.tree:
   row=self.tree.identify_row(e.y)
   if row:
    if row not in self.tree.selection():self.tree.selection_set(row)
    self.selected=row;self.populate();self.refresh_selection()
  else:
   target=self.canvas_target(self.canvas.canvasx(e.x),self.canvas.canvasy(e.y))
   if target:self.selected=target;self.reveal_tree(target);self.populate();self.refresh_selection()
   else:self.selected=None;self.draw()
  menu=tk.Menu(self,tearoff=False)
  if self.selected in getattr(self,'layout_link_rows',{}):
   from layout_links import request_import
   menu.add_command(label=tr('레이아웃 가져오기'),command=lambda:request_import(self))
   try:menu.tk_popup(e.x_root,e.y_root)
   finally:menu.grab_release()
   return
  if self.selected:
   menu.add_command(label=tr('속성'),command=self.open_inspector,state='disabled' if len(self.selected_guids())>1 else 'normal')
   submenu=tk.Menu(menu,tearoff=False)
   for label,action in [(tr('잠그기'),'lock'),(tr('잠금 해제'),'unlock'),(tr('이 대상만 편집'),'others'),(tr('부모 잠그기'),'parent'),(tr('자식 잠그기'),'children'),(tr('전체 잠그기'),'all_lock'),(tr('모든 잠금 해제'),'all_unlock')]:submenu.add_command(label=label,command=lambda a=action:self.lock_action(a))
   menu.add_cascade(label=tr('잠그기'),menu=submenu)
   viewmenu=tk.Menu(menu,tearoff=False)
   for label,action in [(tr('표시 / 숨김'),'toggle'),(tr('자식 보이기'),'children_show'),(tr('자식 숨기기'),'children_hide'),(tr('선택 대상과 자식만 보기'),'only'),(tr('선택한 구성요소만 보기'),'exact'),(tr('전체 숨기기'),'all_hide'),(tr('전체 보이기'),'all_show')]:viewmenu.add_command(label=label,command=lambda a=action:self.view_action(a))
   menu.add_cascade(label=tr('보기'),menu=viewmenu)
   menu.add_separator()
   for label,command in [(tr('잘라내기  Ctrl+X'),self.cut_component),(tr('부모 연결 해제 / no parent'),self.detach_component),(tr('컴포넌트 복사  Ctrl+C'),self.copy_component),(tr('선택한 부모 아래 붙여넣기  Ctrl+V'),self.paste_component),(tr('컴포넌트 삭제  Delete'),self.delete_component),(tr('부모 변경'),self.move_parent_dialog)]:menu.add_command(label=label,command=command,state='disabled' if len(self.selected_guids())>1 else 'normal')
  else:menu.add_command(label=tr('모든 잠금 해제'),command=lambda:self.lock_action('all_unlock'))
  try:menu.tk_popup(e.x_root,e.y_root)
  finally:menu.grab_release()
 def pan_start(self,e):
  if e.state & 4:return 'break'
  c=e.widget;region=list(map(float,c.cget('scrollregion').split()))
  if len(region)==4:
   w,h=c.winfo_width(),c.winfo_height();left,top=c.canvasx(0),c.canvasy(0)
   region=[min(region[0],left-w*2),min(region[1],top-h*2),max(region[2],left+w*3),max(region[3],top+h*3)]
   c.configure(scrollregion=region);c.xview_moveto((left-region[0])/(region[2]-region[0]));c.yview_moveto((top-region[1])/(region[3]-region[1]))
  c.scan_mark(e.x,e.y);c.configure(cursor='fleur');return 'break'
 def pan_move(self,e):
  if not e.state & 4:e.widget.scan_dragto(e.x,e.y,gain=1)
  return 'break'

 def column_widths(self):
  return tuple(self.tree.column(k,'width') for k in ('#0','visibility','locked'))
 def set_column_widths(self,widths):
  for key,width in zip(('#0','visibility','locked'),widths):self.tree.column(key,width=width,stretch=False)
  self.tree.xview_moveto(0)
 def fit_tree_columns(self):
  self.column_job=None
  if self.tree.winfo_width()>10:self.set_column_widths(fit_columns(self.tree.winfo_width()-4,self.column_widths()))
 def column_configure(self,e):
  if self.column_job is None:self.column_job=self.after_idle(self.fit_tree_columns)
 def column_press(self,e):
  if self.tree.identify_region(e.x,e.y)!='separator':return
  widths=self.column_widths();boundaries=(widths[0]+2,widths[0]+widths[1]+2)
  index=min(range(2),key=lambda i:abs(e.x-boundaries[i]))
  if abs(e.x-boundaries[index])>10:return 'break'
  self.column_drag=(index,e.x,widths);return 'break'
 def column_motion(self,e):
  if self.column_drag is None:return
  index,start,widths=self.column_drag
  self.set_column_widths(move_divider(widths,index,e.x-start));return 'break'
 def column_release(self,e):
  if self.column_drag is not None:
   self.column_motion(e);self.column_drag=None;self.save_column_widths();return 'break'
 def save_column_widths(self):
  import json,os
  from pathlib import Path
  self.settings['tree_column_widths']={k:self.tree.column(k,'width') for k in ('#0','visibility','locked')}
  path=Path(os.getenv('APPDATA',str(Path.home())))/'TWUIStudio'/'settings.json'
  try:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(self.settings,ensure_ascii=False),'utf-8')
  except OSError as e:self.status.set(tr('열 너비는 적용했지만 설정 저장 실패: ')+str(e))
