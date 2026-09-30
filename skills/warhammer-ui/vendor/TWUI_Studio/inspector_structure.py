from i18n import tr, trf
"""Structural inspector edits operate only on a local XML draft."""
import re,uuid
from model import Document
from layout_edit import node_end
ORDER=['callbackwithcontextlist','userproperties','componentimages','states','LayoutEngine']

def line_indent(source,node):
 return re.match(r'[ \t]*',source[source.rfind('\n',0,node.start)+1:node.start])[0]

def format_group(source,guid,tag):
 doc=Document(source);component=doc.by_guid[guid];group=component.child(tag)
 if group is None:return source
 nl='\r\n' if '\r\n' in source else '\n'
 base=line_indent(source,group)
 if not base:base=line_indent(source,component)+'\t'
 child=group.children[0] if group.children else None
 child_indent=line_indent(source,child) if child else ''
 unit=child_indent[len(base):] if child_indent.startswith(base) and len(child_indent)>len(base) else '\t'
 edits=[]
 def visit(node,indent):
  token=source[node.start:node.end]
  if node.tag=='property':
   # Change only whitespace before attributes; escaped values remain byte-identical.
   from model import ATTR
   matches=list(ATTR.finditer(token))
   for m in reversed(matches):
    start=m.start()
    while start>0 and token[start-1].isspace():start-=1
    token=token[:start]+nl+indent+unit+token[m.start():]
   edits.append((node.start,node.end,token))
  previous=node.end
  for c in node.children:
   if not source[previous:c.start].strip():edits.append((previous,c.start,nl+indent+unit))
   visit(c,indent+unit);previous=node_end(source,c)
  if hasattr(node,'close_start') and not source[previous:node.close_start].strip():edits.append((previous,node.close_start,nl+indent))
 visit(group,base)
 for a,b,text in sorted(edits,reverse=True):source=source[:a]+text+source[b:]
 return source

def insert_group(source,guid,tag,fragment):
 doc=Document(source);c=doc.by_guid[guid];group=c.child(tag);nl='\r\n' if '\r\n' in source else '\n';base=line_indent(source,c);indent=base+'\t'
 if group is not None:
  if hasattr(group,'close_start'):at=group.close_start;source=source[:at]+nl+indent+'\t'+fragment+nl+indent+source[at:]
  else:source=source[:group.end-2]+'>'+nl+indent+'\t'+fragment+nl+indent+'</'+tag+'>'+source[group.end:]
 else:
  block='<'+tag+'>'+nl+indent+'\t'+fragment+nl+indent+'</'+tag+'>'
  following=next((n for n in c.children if n.tag in ORDER and ORDER.index(n.tag)>ORDER.index(tag)),None)
  if following:at=following.start;source=source[:at]+block+nl+indent+source[at:]
  elif hasattr(c,'close_start'):at=c.close_start;source=source[:at]+nl+indent+block+nl+base+source[at:]
  else:source=source[:c.end-2]+'>'+nl+indent+block+nl+base+'</'+c.tag+'>'+source[c.end:]
 Document(source);return format_group(source,guid,tag)

def edit_section(source,guid,tag,action,index=None):
 doc=Document(source);c=doc.by_guid[guid];group=c.child(tag)
 if action=='add':
  if tag=='callbackwithcontextlist':fragment='<callback_with_context callback_id=""/>'
  elif tag=='componentimages':
   uid=str(uuid.uuid4()).upper();fragment=f'<component_image this="{uid}" uniqueguid="{uid}" imagepath=""/>'
  else:raise ValueError(tr('지원하지 않는 섹션입니다.'))
  return insert_group(source,guid,tag,fragment)
 if group is None:return source
 nodes=[group] if index is None else [group.children[index]]
 if tag=='componentimages':
  removed={n.get('this') for n in (group.children if index is None else nodes)}
  states=c.child('states')
  if states is not None:
   nodes += [n for n in states.descendants() if n.tag=='image' and n.get('componentimage') in removed]
 for node in sorted(nodes,key=lambda n:n.start,reverse=True):source=source[:node.start]+source[node_end(source,node):]
 Document(source);return source
