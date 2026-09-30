"""Lexical whitespace formatting: never serialize or re-escape attribute values."""
import re
from model import TAG, ATTR, Document
from i18n import tr

def format_fragment(source, newline='\n', base=0, multiline=True):
 tokens=list(TAG.finditer(source));cursor=0;depth=base;lines=[];stack=[]
 for m in tokens:
  if source[cursor:m.start()].strip():
   raise ValueError(tr('텍스트 내용이 있는 XML은 자동 정렬할 수 없습니다. 원본을 유지합니다.'))
  token=m[0];special=token.startswith(('<!--','<?'))
  if token.startswith('</'):depth-=1
  indent='\t'*max(0,depth)
  if not special and not token.startswith('</'):
   name=re.match(r'<([^\s/>]+)',token)[1]
   attrs=[a[0] for a in ATTR.finditer(token)]
   ending='/>' if token.endswith('/>') else '>'
   if multiline and attrs and 'hierarchy' not in stack and name!='hierarchy':
    token='<'+name+newline+newline.join(indent+'\t'+a for a in attrs)+ending
   else:token='<'+name+(' '+' '.join(attrs) if attrs else '')+ending
  lines.append(indent+token)
  if not special:
   if token.startswith('</'):
    if stack:stack.pop()
   elif not token.endswith('/>'):
    depth+=1;stack.append(re.match(r'<([^\s/>]+)',token)[1])
  cursor=m.end()
 if source[cursor:].strip():raise ValueError(tr('텍스트 내용이 있는 XML은 자동 정렬할 수 없습니다. 원본을 유지합니다.'))
 return newline.join(lines)

def format_xml(source):
 Document(source)
 newline='\r\n' if '\r\n' in source else '\n'
 result=format_fragment(source,newline)+newline
 Document(result)
 return result

def remove_node(source,node,end):
 start=node.start
 line=source.rfind('\n',0,start)+1
 nextline=source.find('\n',end)
 if not source[line:start].strip() and (nextline<0 or not source[end:nextline].strip()):
  start=line;end=len(source) if nextline<0 else nextline+1
 return source[:start]+source[end:]

def insert_child(source,node,fragment):
 newline='\r\n' if '\r\n' in source else '\n'
 depth=0;p=node.parent
 while p is not None:depth+=1;p=p.parent
 child=format_fragment(fragment,newline,depth+1,False)
 if hasattr(node,'close_start'):
  at=node.close_start
  # Replace only trailing layout whitespace immediately before the closing tag.
  prefix=source[:at].rstrip(' \t\r\n')
  return prefix+newline+child+newline+'\t'*depth+source[at:]
 return source[:node.end-2]+'>'+newline+child+newline+'\t'*depth+'</'+node.tag+'>'+source[node.end:]
