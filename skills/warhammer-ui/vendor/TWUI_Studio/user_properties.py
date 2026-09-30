from i18n import tr, trf
"""Component-level userproperties; unrelated XML is preserved."""
import html,re
from types import SimpleNamespace
from model import Document
from layout_edit import node_end
from component_options import ComponentOptions
from inspector_structure import format_group

def property_values(component):
 node=component.child('userproperties')
 return {p.get('name',''):p.get('value','') for p in node.children if p.tag=='property'} if node is not None else {}

def apply_user_properties(source,guid,values):
 doc=Document(source);component=doc.by_guid[guid];old=property_values(component)
 if old==values:return format_group(source,guid,'userproperties')
 if any(not k.strip() for k in values):raise ValueError(tr('유저 프로퍼티 이름을 입력하세요.'))
 node=component.child('userproperties');patches=[]
 if node is not None:
  for p in node.children:
   if p.tag=='property' and p.get('name') in values and p.get('value','')!=values[p.get('name')]:patches.append((p,{'value':values[p.get('name')]}))
 source=doc.patch(patches);doc=Document(source);component=doc.by_guid[guid];node=component.child('userproperties')
 nl='\r\n' if '\r\n' in source else '\n'
 base=re.match(r'[ \t]*',source[source.rfind('\n',0,component.start)+1:component.start])[0];indent=base+'\t'
 additions=[k for k in values if k not in old]
 def fragment(k):return '<property'+nl+indent+'\t\tname="'+html.escape(k,quote=True)+'"'+nl+indent+'\t\tvalue="'+html.escape(str(values[k]),quote=True)+'"/>'
 edits=[]
 if node is not None:
  removed=[p for p in node.children if p.tag=='property' and p.get('name') not in values]
  if not values and len(removed)==len(node.children):edits.append((node.start,node_end(source,node),''))
  else:
   for p in removed:edits.append((p.start,node_end(source,p),''))
   if additions:
    extra=(nl+indent+'\t').join(fragment(k) for k in additions)
    if hasattr(node,'close_start'):edits.append((node.close_start,node.close_start,'\t'+extra+nl+indent))
    else:edits.append((node.end-2,node.end,'>'+nl+indent+'\t'+extra+nl+indent+'</userproperties>'))
 elif values:
  block='<userproperties>'+nl+indent+'\t'+(nl+indent+'\t').join(fragment(k) for k in additions)+nl+indent+'</userproperties>'
  following=next((n for n in component.children if n.tag in ('componentimages','states','LayoutEngine')),None)
  if following is not None:edits.append((following.start,following.start,block+nl+indent))
  elif hasattr(component,'close_start'):edits.append((component.close_start,component.close_start,'\t'+block+nl+base))
  else:edits.append((component.end-2,component.end,'>'+nl+indent+block+nl+base+'</'+component.tag+'>'))
 for a,b,text in sorted(edits,reverse=True):source=source[:a]+text+source[b:]
 Document(source)
 return format_group(source,guid,'userproperties')

class UserProperties(ComponentOptions):
 def __init__(self,parent,component):
  super().__init__(parent,SimpleNamespace(attrs=property_values(component)),title=tr('유저 프로퍼티 (userproperties)'),catalog_file='user_property_catalog.json',reserved=set(),pair_docking=False)
 def add(self):
  key=self.query.get().strip()
  if not key or key in self.values:return
  self.change(key,self.catalog.get(key,[''])[0]);self.query.set('');self.render()
