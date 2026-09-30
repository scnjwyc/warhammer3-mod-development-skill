from i18n import tr, trf
"""Atomic component-tree edits with consistent GUID remapping."""
import re,uuid
from model import Document,ATTR,TAG
from layout_edit import node_end
from state_edit import append_fragment
REFERENCE_KEYS={'currentstate','defaultstate','componentimage'}

def subtree(doc,guid):
 if guid in getattr(doc,'unlinked_keys',set()) or getattr(doc,'unsafe_keys',set()):raise ValueError(tr('계층 연결 문제를 먼저 확인하세요. XML 구조 검사에서 수정한 뒤 구조를 편집할 수 있습니다.'))
 node=next((n for n in doc.hierarchy.descendants() if n.get('this')==guid),None)
 if node is None:raise ValueError(tr('컴포넌트 계층을 찾을 수 없습니다.'))
 ids=[n.get('this') for n in node.descendants()]
 if any(g not in doc.by_guid for g in ids):raise ValueError(tr('정의가 없는 자식 컴포넌트가 있습니다.'))
 return node,ids

def copied_component(source,guid,target,parent_guid,preserve_name=False):
 src=Document(source);dst=Document(target);hier,ids=subtree(src,guid)
 if parent_guid not in dst.by_guid:raise ValueError(tr('붙여넣을 부모를 선택하세요.'))
 used={dst.by_guid[g].get('id') for g in dst.children.get(parent_guid,[])}|{c.get('id') for c in src.components}
 base=src.by_guid[guid].get('id','component');index=1
 while f'{base}_copy_{index}' in used:index+=1
 name=base if preserve_name else f'{base}_copy_{index}'
 if preserve_name and any(dst.by_guid[g].get('id')==name for g in dst.children.get(parent_guid,[])):raise ValueError(tr('부모 아래에 같은 이름의 컴포넌트가 이미 있습니다.'))
 renamed=src.rename(guid,name);src=Document(renamed);hier,ids=subtree(src,guid)
 nodes=[n for g in ids for n in src.by_guid[g].descendants()]
 declarations={n.get(k) for n in nodes for k in ('this','uniqueguid') if n.get(k)}
 occupied={n.get(k) for n in dst.nodes for k in ('this','uniqueguid') if n.get(k)}
 mapping={}
 for old in declarations:
  fresh=str(uuid.uuid4()).upper()
  while fresh in occupied:fresh=str(uuid.uuid4()).upper()
  mapping[old]=fresh;occupied.add(fresh)
 for node in nodes:
  for key in REFERENCE_KEYS:
   ref=node.get(key)
   if ref and ref not in mapping and ref not in occupied:raise ValueError(trf('복사 범위 밖의 {0} 연결이 있습니다. 연결된 컴포넌트를 포함하는 부모를 복사하세요.', key))
 def remap(fragment):
  def token(m):
   if m[0].startswith(('<!--','<?','</')):return m[0]
   def attribute(a):
    value=mapping.get(a[3])
    return a[0][:a.start(3)-a.start()]+value+a[0][a.end(3)-a.start():] if value else a[0]
   return ATTR.sub(attribute,m[0])
  return TAG.sub(token,fragment)
 definitions='\n'.join(remap(renamed[src.by_guid[g].start:node_end(renamed,src.by_guid[g])]) for g in ids)
 hierarchy=remap(renamed[hier.start:node_end(renamed,hier)])
 result=append_fragment(target,dst.root.child('components'),definitions)
 dst=Document(result);parent=next(n for n in dst.hierarchy.descendants() if n.get('this')==parent_guid)
 result=append_fragment(result,parent,hierarchy);Document(result)
 return result,mapping[guid]

def deleted_component(source,guid):
 doc=Document(source);hier,ids=subtree(doc,guid)
 if not doc.parents.get(guid):raise ValueError(tr('문서의 최상위 root는 삭제할 수 없습니다.'))
 removed_nodes={n for g in ids for n in doc.by_guid[g].descendants()};removed_ids={n.get('this') for n in removed_nodes}
 for n in doc.nodes:
  if n not in removed_nodes and any(n.get(k) in removed_ids for k in REFERENCE_KEYS if n.get(k)):raise ValueError(tr('다른 컴포넌트에서 참조하는 항목입니다. 연결을 먼저 변경하세요.'))
 ranges=[(hier.start,node_end(source,hier))]+[(doc.by_guid[g].start,node_end(source,doc.by_guid[g])) for g in ids]
 for a,b in sorted(ranges,reverse=True):source=source[:a]+source[b:]
 Document(source);return source

def moved_component(source,guid,parent_guid):
 doc=Document(source);hier,ids=subtree(doc,guid)
 if not doc.parents.get(guid):raise ValueError(tr('최상위 root는 이동할 수 없습니다.'))
 if parent_guid in ids:raise ValueError(tr('자기 자신이나 자손 아래로 이동할 수 없습니다.'))
 if parent_guid not in doc.by_guid:raise ValueError(tr('부모를 찾을 수 없습니다.'))
 if doc.parents.get(guid)==parent_guid:return source
 name=doc.by_guid[guid].get('id')
 if any(doc.by_guid[g].get('id')==name for g in doc.children.get(parent_guid,[])):raise ValueError(tr('새 부모 아래에 같은 ID가 있습니다. 먼저 ID를 변경하세요.'))
 fragment=source[hier.start:node_end(source,hier)];result=source[:hier.start]+source[node_end(source,hier):]
 doc=Document(result);parent=next(n for n in doc.hierarchy.descendants() if n.get('this')==parent_guid)
 result=append_fragment(result,parent,fragment);Document(result);return result

def reordered_children(source,parent_guid,order):
 """Reorder complete direct-child hierarchy blocks; definitions stay untouched."""
 doc=Document(source);parent,_=subtree(doc,parent_guid)
 children=parent.children;current=[n.get('this') for n in children]
 if len(order)!=len(current) or len(set(order))!=len(order) or set(order)!=set(current):
  raise ValueError('Children order must contain each direct child exactly once.')
 if list(order)==current:return source
 blocks={n.get('this'):source[n.start:node_end(source,n)] for n in children}
 result=source
 for old,new in reversed(list(zip(children,order))):
  result=result[:old.start]+blocks[new]+result[node_end(source,old):]
 Document(result)
 return result
