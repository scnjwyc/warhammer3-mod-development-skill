"""Source-preserving hierarchy edits. Definitions and GUIDs are never regenerated."""
import html
from model import Document
from layout_edit import node_end
from xml_format import insert_child as append_fragment, remove_node
from i18n import tr
NO_PARENT='@no_parent_group'

def node_for(doc,key):
 if key not in doc.by_guid:raise ValueError(tr('컴포넌트를 선택하세요.'))
 return doc.hierarchy_nodes[key]

def ensure_unique(doc,key):
 c=doc.by_guid.get(key)
 if c is None or key in doc.placeholder_keys or c.get('this')!=key or sum(x.get('this')==key for x in doc.components)!=1:
  raise ValueError(tr('GUID 연결을 먼저 확인하세요.'))
 if sum(n.get('this')==key for n in doc.raw_hierarchy.descendants())>1:raise ValueError(tr('GUID 연결을 먼저 확인하세요.'))

def remove_missing(doc,key):
 """Remove only the missing wrapper. Any children remain in their original order."""
 if key not in doc.missing_keys:raise ValueError(tr('정의가 없는 계층 항목을 선택하세요.'))
 n=node_for(doc,key);end=node_end(doc.source,n)
 inside=doc.source[n.end:n.close_start] if hasattr(n,'close_start') else ''
 result=doc.source[:n.start]+inside+doc.source[end:]
 Document(result);return result

def detach(source,key):
 doc=Document(source);ensure_unique(doc,key)
 if key in doc.unlinked_keys:return source
 n=node_for(doc,key)
 result=remove_node(source,n,node_end(source,n))
 Document(result);return result

def move(source,key,parent):
 doc=Document(source);ensure_unique(doc,key);ensure_unique(doc,parent)
 if key==parent:raise ValueError(tr('자기 자신이나 자손 아래로 이동할 수 없습니다.'))
 if key not in doc.unlinked_keys:
  n=node_for(doc,key)
  if any(ch.get('this')==parent for ch in n.descendants()):raise ValueError(tr('자기 자신이나 자손 아래로 이동할 수 없습니다.'))
  if doc.parents.get(key)==parent:return source
  fragment=source[n.start:node_end(source,n)]
  result=remove_node(source,n,node_end(source,n))
 else:
  c=doc.by_guid[key];fragment='<'+c.tag+' this="'+html.escape(key,quote=True)+'"/>';result=source
 doc=Document(result)
 if parent in doc.unlinked_keys:
  c=doc.by_guid[parent];result=append_fragment(result,doc.raw_hierarchy,'<'+c.tag+' this="'+html.escape(parent,quote=True)+'"/>')
  doc=Document(result)
 result=append_fragment(result,node_for(doc,parent),fragment)
 Document(result);return result
