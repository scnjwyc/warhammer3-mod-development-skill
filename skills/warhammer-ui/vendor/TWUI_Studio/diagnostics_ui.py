"""Identity warning UI; repairs are explicit, atomic, undoable editor actions."""
import tkinter as tk
from tkinter import ttk, messagebox
from i18n import tr
from diagnostics import repair_hierarchy_guids, repair_duplicate_guids, highest_severity, SEVERITY_COLORS, marker_kind

class HoverNote:
 def __init__(self,widget,lookup):
  self.widget=widget;self.lookup=lookup;self.tip=None;self.text=None
  widget.bind('<Motion>',self.move,add='+');widget.bind('<Leave>',self.hide,add='+')
  widget.bind('<ButtonPress>',self.hide,add='+');widget.bind('<Destroy>',self.hide,add='+')
 def hide(self,event=None):
  if self.tip is not None:
   try:self.tip.destroy()
   except tk.TclError:pass
  self.tip=None;self.text=None
 def move(self,event):
  text=self.lookup(event)
  if text==self.text:return
  self.hide()
  if not text:return
  self.text=text;self.tip=tk.Toplevel(self.widget);self.tip.overrideredirect(True)
  ttk.Label(self.tip,text=text,wraplength=470,padding=8,relief='solid').pack()
  self.tip.geometry('+%d+%d'%(max(0,min(event.x_root+15,self.widget.winfo_screenwidth()-500)),max(0,min(event.y_root+18,self.widget.winfo_screenheight()-130))))

def issue_text(issues):return '\n'.join(dict.fromkeys(i.message for i in issues))

def install_tree_warnings(app):
 if hasattr(app,'diagnostic_icons'):return
 app.diagnostic_icons={}
 for level,color in SEVERITY_COLORS.items():
  icon=tk.PhotoImage(master=app.tree,width=13,height=13)
  for y in range(1,12):
   left=max(0,6-y//2);right=min(12,6+y//2)
   icon.put(color,to=(left,y,right+1,y+1))
  ink='white' if level=='error' else '#20242c'
  icon.put(ink,to=(6,4,7,8));icon.put(ink,to=(6,9,7,10))
  app.diagnostic_icons[level]=icon
 icon=tk.PhotoImage(master=app.tree,width=13,height=13)
 for y,row in enumerate(('01110','11011','00011','00110','01100','01100','00000','01100'),2):
  for x,v in enumerate(row,4):
   if v=='1':icon.put('#ec4d55',to=(x,y))
 app.diagnostic_icons['missing']=icon
 app.diagnostic_hover=HoverNote(app.tree,lambda e:issue_text(app.doc.issues_by_key.get(app.tree.identify_row(e.y),[])))

def show_diagnostics(app,initial=False):
 win=tk.Toplevel(app);win.title(tr('XML 구조 검사'));win.geometry('870x480');win.minsize(650,350);win.transient(app)
 ttk.Label(win,text=tr('계층 연결 문제를 표시합니다. 사소한 차이와 미사용 정의는 도움말의 XML 구조 검사에서 확인할 수 있습니다.') if initial else tr('XML 구조 검사 · 빨강: 연결 문제 / 노랑: 사소한 차이 / 회색: 계층에서 미사용'),wraplength=820,padding=10).pack(fill='x')
 area=ttk.Frame(win);area.pack(fill='both',expand=True,padx=10)
 table=ttk.Treeview(area,columns=('line','name','issue'),show='tree headings',selectmode='browse')
 table.column('#0',width=25,stretch=False)
 install_tree_warnings(app)
 for key,label,width in [('line',tr('줄'),55),('name',tr('컴포넌트'),190),('issue',tr('문제 설명'),560)]:
  table.heading(key,text=label);table.column(key,width=width,stretch=key=='issue')
 bar=ttk.Scrollbar(area,orient='vertical',command=table.yview);table.configure(yscrollcommand=bar.set)
 bar.pack(side='right',fill='y');table.pack(fill='both',expand=True)
 detail=tk.StringVar();ttk.Label(win,textvariable=detail,wraplength=820,padding=10).pack(fill='x')
 buttons=ttk.Frame(win,padding=10);buttons.pack(fill='x')
 def refresh():
  table.delete(*table.get_children())
  remove.configure(state='disabled')
  for i,item in enumerate(app.doc.issues):
   if initial and item.severity!='error':continue
   node=item.nodes[0];line=app.doc.source.count('\n',0,node.start)+1
   table.insert('','end',iid=str(i),image=app.diagnostic_icons[marker_kind([item])],values=(line,node.get('id',node.tag),item.message))
  hierarchy.configure(state='normal' if app.doc.guid_repairs else 'disabled')
  duplicates.configure(state='normal' if app.doc.duplicate_repairs or app.doc.guid_repairs else 'disabled')
  detail.set(tr('GUID 수정은 고유한 이름으로 연결이 확인된 항목에만 적용됩니다. 중복 재배정은 중복된 말단 계층 참조의 정의를 복제합니다. 판단할 수 없는 문제는 남겨둡니다.') if any(not initial or i.severity=='error' for i in app.doc.issues) else tr('표시할 연결 문제가 없습니다.'))
 def select(event=None):
  if not table.selection():return
  item=app.doc.issues[int(table.selection()[0])]
  remove.configure(state='normal' if any(k in app.doc.missing_keys for k in item.keys) else 'disabled')
  if item.keys:
   app.selected=item.keys[0];app.reveal_tree(app.selected);app.populate();app.refresh_selection()
  app.xml_viewer.reveal(item.nodes[0]);detail.set(item.message+'\n'+tr('관련 줄')+': '+', '.join(str(app.doc.source.count('\n',0,n.start)+1) for n in item.nodes))
 def repair(fn,label):
  try:
   source=fn(app.doc)
   app.commit(source,label);refresh()
  except Exception as exc:messagebox.showerror(tr('변경 실패'),str(exc),parent=win)
 def remove_selected():
  if not table.selection():return
  item=app.doc.issues[int(table.selection()[0])]
  key=next((k for k in item.keys if k in app.doc.missing_keys),None)
  if key is None:return
  from hierarchy_edit import remove_missing
  repair(lambda doc:remove_missing(doc,key),tr('정의 없는 계층만 삭제'))
 remove=ttk.Button(buttons,text=tr('선택한 계층만 삭제'),command=remove_selected,state='disabled');remove.pack(side='left',padx=5)
 hierarchy=ttk.Button(buttons,text=tr('하이어라키 GUID로 통일'),command=lambda:repair(repair_hierarchy_guids,tr('하이어라키 GUID 수정')));hierarchy.pack(side='left')
 duplicates=ttk.Button(buttons,text=tr('중복 GUID 재배정'),command=lambda:repair(repair_duplicate_guids,tr('중복 GUID 재배정')));duplicates.pack(side='left',padx=5)
 ttk.Button(buttons,text=tr('닫기'),command=win.destroy).pack(side='right')
 table.bind('<<TreeviewSelect>>',select);HoverNote(table,lambda e:app.doc.issues[int(table.identify_row(e.y))].message if table.identify_row(e.y) else '')
 refresh();win.grab_set();app.wait_window(win)
