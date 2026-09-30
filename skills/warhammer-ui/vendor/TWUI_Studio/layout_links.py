"""Explicit ComponentCreator layout imports; never load files during canvas rendering."""
import base64,json,re
from i18n import tr,trf
from pathlib import Path
from model import Document,Resources
from component_edit import copied_component
from state_edit import append_fragment
MARKER=re.compile(r'<!-- TWUIStudio-layout ([A-Za-z0-9+/=]+) -->')

def layout_refs(doc):
 result=[]
 for c in doc.components:
  for n in c.descendants():
   if n.get('callback_id')!='ComponentCreator':continue
   for p in n.descendants():
    if p.tag=='property' and p.get('name')=='layout' and p.get('value'):
     item=(c.get('this'),p.get('value'))
     if item not in result:result.append(item)
 return result

def imported_links(doc):
 result={}
 for m in MARKER.finditer(doc.source):
  try:
   value=json.loads(base64.b64decode(m[1]).decode('utf-8'))
   if all(isinstance(value.get(k),str) for k in ('creator','path','root')) and value['root'] in doc.by_guid:result[(value['creator'],value['path'])]=value['root']
  except (ValueError,UnicodeError,TypeError,AttributeError):pass
 return result

def layout_name(ref):
 name=ref.replace('\\','/').rsplit('/',1)[-1]
 for ext in ('.twui.xml','.xml'):
  if name.lower().endswith(ext):return name[:-len(ext)]
 return name

def resolve_layout(root,ref):
 resolver=Resources([root]);names=[ref] if ref.lower().endswith('.xml') else [ref+'.twui.xml',ref+'.xml',ref]
 for name in names:
  path=resolver.resolve(name)
  if path:return path
 raise ValueError(tr('원본 UI 리소스에서 레이아웃을 찾을 수 없습니다: ')+ref)

def import_layout(source,creator,ref,external):
 dst=Document(source)
 if (creator,ref) not in layout_refs(dst):raise ValueError(tr('현재 문서에 해당 ComponentCreator 연결이 없습니다.'))
 if (creator,ref) in imported_links(dst):raise ValueError(tr('이미 가져온 레이아웃입니다.'))
 src=Document(external);roots=[n.get('this') for n in src.hierarchy.children if n.get('this') not in src.unlinked_keys]
 if len(roots)!=1:raise ValueError(tr('가져올 레이아웃에는 하나의 최상위 계층이 필요합니다.'))
 external=src.rename(roots[0],layout_name(ref))
 result,newkey=copied_component(external,roots[0],source,creator,preserve_name=True)
 marker=base64.b64encode(json.dumps(dict(creator=creator,path=ref,root=newkey),ensure_ascii=False).encode()).decode()
 result=append_fragment(result,Document(result).root,'<!-- TWUIStudio-layout '+marker+' -->')
 Document(result);return result,newkey

def link_icons(app):
 from PIL import Image,ImageDraw,ImageTk
 if hasattr(app,'layout_link_icons'):return app.layout_link_icons
 icons={}
 for pending in (False,True):
  im=Image.new('RGBA',(34 if pending else 17,16));d=ImageDraw.Draw(im)
  d.rounded_rectangle((1,5,10,12),radius=3,outline='#688498',width=2)
  d.rounded_rectangle((7,1,16,8),radius=3,outline='#688498',width=2)
  if pending:
   d.line([(20,10),(20,14),(32,14),(32,10)],fill='#527c95',width=2)
   d.line([(26,1),(26,10),(22,6)],fill='#527c95',width=2);d.line([(26,10),(30,6)],fill='#527c95',width=2)
  icons[pending]=ImageTk.PhotoImage(im,master=app)
 app.layout_link_icons=icons;return icons

def decorate_tree(app):
 refs=layout_refs(app.doc);origins=imported_links(app.doc);app.layout_link_rows={}
 if not refs and not origins:return
 icons=link_icons(app);app.tree.tag_configure('layout_pending',foreground='#929292')
 for key in origins.values():
  if app.tree.exists(key):app.tree.item(key,image=icons[False])
 for i,(creator,path) in enumerate(refs):
  if (creator,path) in origins or not app.tree.exists(creator):continue
  row='@layout_link:'+str(i);app.layout_link_rows[row]=(creator,path)
  app.tree.insert(creator,'end',iid=row,text=layout_name(path),image=icons[True],tags=('layout_pending',))

def request_import(app):
 from tkinter import messagebox
 item=getattr(app,'layout_link_rows',{}).get(app.selected)
 if not item:return 'break'
 if not app.document_switch_allowed():return 'break'
 creator,ref=item
 try:path=resolve_layout(app.settings.get('resource',''),ref)
 except (OSError,ValueError) as e:messagebox.showerror(tr('레이아웃 가져오기'),str(e),parent=app);return 'break'
 if not messagebox.askokcancel(tr('레이아웃 가져오기'),trf('{0}\n\n이 레이아웃을 현재 XML의 자식으로 복사할까요?\n실행 취소할 수 있습니다. 기존 ComponentCreator 콜백은 유지됩니다.',ref),parent=app):return 'break'
 try:
  source,key=import_layout(app.doc.source,creator,ref,path.read_text('utf-8-sig'))
  app.commit(source,'레이아웃 가져오기');app.selected=key;app.reveal_tree(key);app.populate();app.refresh_selection()
 except (OSError,ValueError) as e:messagebox.showerror(tr('레이아웃 가져오기'),str(e),parent=app)
 return 'break'
