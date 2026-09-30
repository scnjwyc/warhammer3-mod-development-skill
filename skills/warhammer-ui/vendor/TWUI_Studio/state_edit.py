from i18n import tr, trf
import re,uuid,html
from model import Document,ATTR
from layout_edit import node_end

def new_guid():return str(uuid.uuid4()).upper()
def append_fragment(source,node,fragment):
 newline='\r\n' if '\r\n' in source else '\n'
 if hasattr(node,'close_start'):
  at=node.close_start;return source[:at]+newline+fragment+newline+source[at:]
 return source[:node.end-2]+'>'+newline+fragment+newline+'</'+node.tag+'>'+source[node.end:]
def state_node(doc,component_guid,state_guid):
 states=doc.by_guid[component_guid].child('states')
 return next((s for s in states.children if s.get('this')==state_guid),None) if states else None

def add_state(source,component_guid,copy_guid=None):
 doc=Document(source);component=doc.by_guid[component_guid];states=component.child('states')
 old=state_node(doc,component_guid,copy_guid) if copy_guid else None;guid=new_guid()
 existing={s.get('name',s.tag) for s in states.children} if states else set();index=1
 while f'NewState_{index}' in existing:index+=1
 name=f'NewState_{index}'
 if old is not None:
  fragment=source[old.start:node_end(source,old)]
  mapping={n.get('this'):new_guid() for n in old.descendants() if n.get('this')};mapping[old.get('this')]=guid
  # Replace GUID-valued attributes only; componentimage points outside this subtree.
  fragment=ATTR.sub(lambda m:m[0][:m.start(3)-m.start()]+mapping[m[3]]+m[0][m.end(3)-m.start():] if m[3] in mapping and m[1]!='componentimage' else m[0],fragment)
  opening=fragment[:old.end-old.start]
  match=next((m for m in ATTR.finditer(opening) if m[1]=='name'),None)
  if match:fragment=fragment[:match.start(3)]+name+fragment[match.end(3):]
  else:
   at=len(opening)-(2 if opening.endswith('/>') else 1);fragment=fragment[:at]+' name="'+name+'"'+fragment[at:]
 else:fragment=f'<newstate this="{guid}" uniqueguid="{guid}" name="{name}" width="100.00" height="30.00"/>'
 from inspector_structure import insert_group
 result=insert_group(source,component_guid,'states',fragment)
 doc=Document(result);c=doc.by_guid[component_guid]
 attrs={k:guid for k in ('currentstate','defaultstate') if not c.get(k)}
 return doc.patch([(c,attrs)]),guid

def add_state_child(source,component_guid,state_guid,kind,image_guid=None):
 doc=Document(source);state=state_node(doc,component_guid,state_guid)
 if state is None:raise ValueError(tr('편집할 상태를 선택하세요.'))
 if kind=='text':
  if state.child('component_text') is not None:return source
  fragment='<component_text text="" textlabel=""/>';parent=state
 else:
  c=doc.by_guid[component_guid];images=c.child('componentimages')
  if images is None or image_guid not in {n.get('this') for n in images.children}:raise ValueError(tr('먼저 연결할 컴포넌트 이미지가 있어야 합니다.'))
  guid=new_guid();fragment=f'<image this="{guid}" uniqueguid="{guid}" componentimage="{image_guid}" width="{state.get("width","100")}" height="{state.get("height","30")}"/>'
  parent=state.child('imagemetrics')
  if parent is None:fragment='<imagemetrics>'+fragment+'</imagemetrics>';parent=state
 result=append_fragment(source,parent,fragment);Document(result);return result

def merge_states(source,draft,component_guid):
 target=Document(source);edited=Document(draft);a=target.by_guid[component_guid];b=edited.by_guid[component_guid]
 old=a.child('states');new=b.child('states')
 if new is not None:
  fragment=draft[new.start:node_end(draft,new)]
  if old is not None:source=source[:old.start]+fragment+source[node_end(source,old):]
  else:source=append_fragment(source,a,fragment)
 elif old is not None:source=source[:old.start]+source[node_end(source,old):]
 doc=Document(source);a=doc.by_guid[component_guid]
 return doc.patch([(a,{k:b.get(k) for k in ('currentstate','defaultstate') if a.get(k)!=b.get(k)})])

def remove_state(source,component_guid,state_guid):
 doc=Document(source);state=state_node(doc,component_guid,state_guid)
 if state is None:return source
 states=doc.by_guid[component_guid].child('states');remaining=[s for s in states.children if s is not state]
 node=state if remaining else states
 source=source[:node.start]+source[node_end(source,node):]
 doc=Document(source);c=doc.by_guid[component_guid];fallback=remaining[0].get('this') if remaining else None
 return doc.patch([(c,{k:fallback for k in ('currentstate','defaultstate') if c.get(k)==state_guid})])

def remove_state_child(source,component_guid,state_guid,index):
 doc=Document(source);state=state_node(doc,component_guid,state_guid)
 if state is None:return source
 node=list(state.descendants())[index]
 if node is state:raise ValueError(tr('상태 삭제 버튼을 사용하세요.'))
 return source[:node.start]+source[node_end(source,node):]
