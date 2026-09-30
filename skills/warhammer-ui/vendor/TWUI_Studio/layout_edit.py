from i18n import tr, trf
import html,re
from model import Document

def apply_layout(source,guid,values):
 doc=Document(source);component=doc.by_guid[guid];node=component.child('LayoutEngine')
 if node is not None:
  changes={k:values.get(k) for k in node.attrs.keys()|values.keys() if node.get(k)!=values.get(k)}
  return doc.patch([(node,changes)]) if changes else source
 if not values:return source
 if not hasattr(component,'close_start'):raise ValueError(tr('LayoutEngine을 추가할 컴포넌트의 닫는 태그가 없습니다.'))
 newline='\r\n' if '\r\n' in source else '\n'
 start=source.rfind('\n',0,component.close_start)+1
 indent=re.match(r'[ \t]*',source[start:component.close_start])[0]
 text='<LayoutEngine'+''.join(' '+k+'="'+html.escape(str(v),quote=True)+'"' for k,v in values.items())+'/>'
 at=component.close_start
 result=source[:at]+'\t'+text+newline+indent+source[at:]
 Document(result)
 return result

def node_end(source,node):
 return source.index('>',node.close_start)+1 if hasattr(node,'close_start') else node.end

def apply_layout_settings(source,guid,values):
 from layout_options import column_values
 values=dict(values);columns=values.pop('columnwidths',None)
 doc=Document(source);node=doc.by_guid[guid].child('LayoutEngine')
 if not values.get('type'):
  return source[:node.start]+source[node_end(source,node):] if node is not None else source
 widths=column_values(columns) if columns is not None else None
 result=apply_layout(source,guid,values);doc=Document(result);node=doc.by_guid[guid].child('LayoutEngine');old=node.child('columnwidths')
 if old is not None and widths==[c.get('width') for c in old.children]:return result
 if old is None and widths is None:return result
 fragment='<columnwidths>'+''.join('<column width="'+w+'"/>' for w in widths)+'</columnwidths>' if widths is not None else ''
 if old is not None:result=result[:old.start]+fragment+result[node_end(result,old):]
 elif hasattr(node,'close_start'):result=result[:node.close_start]+fragment+result[node.close_start:]
 else:result=result[:node.end-2]+'>'+fragment+'</LayoutEngine>'+result[node.end:]
 Document(result)
 return format_layout(result,guid)


def format_layout(source,guid):
 doc=Document(source);layout=doc.by_guid[guid].child('LayoutEngine')
 if layout is None:return source
 newline='\r\n' if '\r\n' in source else '\n'
 prefix=source[source.rfind('\n',0,layout.start)+1:layout.start]
 base=re.match(r'[ \t]*',prefix)[0]
 token=source[layout.start:layout.end]
 match=re.search(r'\n([ \t]+)\w',token)
 deeper=match[1] if match else ''
 unit=deeper[len(base):] if deeper.startswith(base) and len(deeper)>len(base) else ('\t' if '\t' in base else '    ')
 edits=[]
 def gap(a,b,indent):
  if not source[a:b].strip():edits.append((a,b,newline+indent))
 def visit(node,indent):
  previous=node.end
  for child in node.children:
   gap(previous,child.start,indent+unit);visit(child,indent+unit);previous=node_end(source,child)
  if hasattr(node,'close_start'):gap(previous,node.close_start,indent)
 visit(layout,base)
 for a,b,value in sorted(edits,reverse=True):source=source[:a]+value+source[b:]
 return source
