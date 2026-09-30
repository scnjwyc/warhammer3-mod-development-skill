from i18n import tr, trf
"""TWUI lexical model: only edited attributes are patched; original bytes survive."""
import re, html
import xml.etree.ElementTree as ET
from pathlib import Path
TAG = re.compile(r'<!--[\s\S]*?-->|<\?[\s\S]*?\?>|</?[A-Za-z_][\w:.-]*(?:"[^"]*"|\'[^\']*\'|[^\'">])*>')
ATTR = re.compile(r'([\w:.-]+)\s*=\s*([\"\'])(.*?)\2', re.S)
# XML entities only: html.unescape would also decode bare CCO text such as &not.
XML_ENTITY = re.compile(r'&(?:amp|lt|gt|quot|apos|#[0-9]+|#x[0-9a-fA-F]+);')
BARE_AMP = re.compile(r'&(?!amp;|lt;|gt;|quot;|apos;|#[0-9]+;|#x[0-9a-fA-F]+;)')
def attribute_value(value):
 return XML_ENTITY.sub(lambda m: html.unescape(m[0]), value)
def validation_source(source):
 # Normalize a validation copy only; lexical offsets and saved source stay intact.
 def tag(match):
  token=match[0]
  if token.startswith(('<!--','<?','</')):return token
  def attribute(a):
   value=BARE_AMP.sub('&amp;',a[3]).replace('<','&lt;')
   return a[0][:a.start(3)-a.start()]+value+a[0][a.end(3)-a.start():]
  return ATTR.sub(attribute,token)
 return TAG.sub(tag,source)
def pair(s, default=(0.,0.)):
 try: return tuple(float(x) for x in s.split(','))
 except (ValueError,AttributeError): return default
def number(s, default=0.):
 try:return float(s)
 except (ValueError,TypeError):return default
class Node:
 def __init__(self,tag,start,end,attrs,parent=None):
  self.tag,self.start,self.end,self.attrs,self.parent=tag,start,end,attrs,parent
  self.children=[]
 def get(self,k,d=None):return self.attrs.get(k,d)
 def child(self,name):return next((c for c in self.children if c.tag==name),None)
 def descendants(self):
  yield self
  for c in self.children:yield from c.descendants()
class Document:
 def __init__(self,source):
  self.source=source;self.nodes=[];stack=[]
  # Game/CCO attributes may contain literal && and <; validate without rewriting.
  ET.fromstring(validation_source(source))
  for m in TAG.finditer(source):
   token=m[0]
   if token.startswith(('<!--','<?')):continue
   if token.startswith('</'):
    closed=stack.pop();closed.close_start=m.start();continue
   tag=re.match(r'<([\w:.-]+)',token)[1]
   n=Node(tag,m.start(),m.end(),{a[1]:attribute_value(a[3]) for a in ATTR.finditer(token)},stack[-1] if stack else None)
   if stack:stack[-1].children.append(n)
   self.nodes.append(n)
   if not token.endswith('/>'):stack.append(n)
  self.root=self.nodes[0]; container=self.root.child('components'); h=self.root.child('hierarchy')
  if container is None or h is None:raise ValueError(tr('TWUI layout의 hierarchy/components가 없습니다.'))
  self.components=container.children
  from diagnostics import inspect_document
  inspect_document(self,h)
 def state(self,c):
  ss=c.child('states')
  if ss is None:return None
  return next((s for s in ss.children if s.get('this')==c.get('currentstate',c.get('defaultstate'))),ss.children[0] if ss.children else None)
 def rename(self,guid,name):
  c=self.by_guid[guid]
  if name==c.get('id'):return self.source
  if not re.fullmatch(r'[A-Za-z_][\w.()\-]*',name):raise ValueError(tr('ID는 영문/밑줄로 시작하고 문자, 숫자, 밑줄, 점, 하이픈, 괄호만 사용할 수 있습니다.'))
  from diagnostics import name_tag
  tag_name=name_tag(name)
  if guid in self.unsafe_keys:raise ValueError(tr('계층 연결 문제를 먼저 확인하세요. XML 구조 검사에서 수정한 뒤 구조를 편집할 수 있습니다.'))
  siblings=self.children.get(self.parents.get(guid),[n.get('this') for n in self.hierarchy.children])
  if any(g!=guid and self.by_guid.get(g) is not None and self.by_guid[g].get('id')==name for g in siblings):raise ValueError(tr('같은 부모 아래에 동일한 ID가 있습니다.'))
  doc=Document(self.patch([(c,{'id':name})]));changes=[]
  nodes=[doc.by_guid[guid]]+[n for n in doc.hierarchy.descendants() if n.get('this')==guid]
  for n in {n.start:n for n in nodes}.values():
   changes.append((n.start+1,n.start+1+len(n.tag),tag_name))
   if hasattr(n,'close_start'):changes.append((n.close_start+2,n.close_start+2+len(n.tag),tag_name))
  result=doc.source
  for a,b,v in sorted(changes,reverse=True):result=result[:a]+v+result[b:]
  Document(result)
  return result
 def patch(self,changes):
  replacements=[]
  for node,values in changes:
   if getattr(node,'placeholder',False):raise ValueError(tr('정의가 없는 임시 항목은 XML 구조 검사에서 연결을 먼저 확인하세요.'))
   token=self.source[node.start:node.end]
   for key,value in values.items():
    match=next((m for m in ATTR.finditer(token) if m[1]==key),None)
    if value is None:
     if match:
      start=match.start()
      while start>0 and token[start-1].isspace():start-=1
      token=token[:start]+token[match.end():]
     continue
    value=str(value)
    escaped=html.escape(value,quote=True)
    if match:token=token[:match.start(3)]+escaped+token[match.end(3):]
    else:
     at=len(token)-(2 if token.endswith('/>') else 1)
     attrs=list(ATTR.finditer(token))
     newline='\r\n' if '\r\n' in self.source else '\n'
     indent_match=re.search(r'\n([ \t]+)\w[\w:.-]*\s*=',token)
     line_start=self.source.rfind('\n',0,node.start)+1
     base=re.match(r'[ \t]*',self.source[line_start:node.start])[0]
     indent=indent_match[1] if indent_match else base+'\t'
     addition=key+'="'+escaped+'"'
     before=next((a for a in attrs if a[1]=='uniqueguid'),None) if key=='tooltiplabel' else None
     if before:
      # Reuse the existing indentation before uniqueguid, then repeat it after the new attribute.
      prefix=token[:before.start()]
      if prefix[prefix.rfind('\n')+1:].strip():prefix=prefix.rstrip(' \t')+newline+indent
      token=prefix+addition+newline+indent+token[before.start():]
     elif key=='tooltiplabel' or '\n' in token:
      anchor=next((a for a in reversed(attrs) if a[1] in ('priority','this')),None) if key=='tooltiplabel' else None
      if anchor:
       at=anchor.end();token=token[:at]+newline+indent+addition+token[at:]
      else:token=token[:at]+newline+indent+addition+token[at:]
     else:token=token[:at]+' '+addition+token[at:]
   replacements.append((node.start,node.end,token))
  result=self.source
  for a,b,v in sorted(replacements,reverse=True):result=result[:a]+v+result[b:]
  return result
def clean_resource_path(value):
 # Windows Explorer's Copy as path can include quotes and direction marks.
 return str(value).translate(dict.fromkeys(map(ord,'\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069'))).strip().strip('"').strip()

def resource_root(value):
 """Use the same effective ui directory in the browser and image resolver."""
 value=clean_resource_path(value)
 if not value:return None
 root=Path(value)
 # Extracted archives can create ui/ui. The browser has always entered this
 # child, whereas the resolver previously searched the outer ui directory.
 try:
  if (root/'ui').is_dir():root=root/'ui'
 except OSError:pass
 return root

class Resources:
 def __init__(self,roots):
  self.roots=list(dict.fromkeys(root for r in roots if (root:=resource_root(r)) is not None));self.cache={};self.directories={}
 def locate(self,root,parts):
  candidate=root.joinpath(*parts)
  if candidate.is_file():return candidate
  # Resolve each directory segment, retaining its actual spelling. Never use
  # a global basename search: DLC folders may contain different same-name files.
  current=root
  for part in parts:
   direct=current/part
   if direct.exists():current=direct;continue
   if current not in self.directories:
    try:
     table={}
     for child in current.iterdir():table.setdefault(child.name.casefold(),[]).append(child)
     self.directories[current]=table
    except OSError:return None
   matches=self.directories[current].get(part.casefold(),[])
   if len(matches)!=1:return None
   current=matches[0]
  return current if current.is_file() else None
 def candidates(self,path):
  path=clean_resource_path(path).replace('\\','/')
  parts=tuple(p for p in path.split('/') if p and p!='.')
  if not parts or path.startswith('/') or '..' in parts or any(':' in p for p in parts):return []
  relative=parts[1:] if parts[0].casefold()=='ui' else parts
  result=[]
  for root in self.roots:
   if root.name.casefold()=='ui':result.append((root,relative))
   elif root.name.casefold()=='default' and tuple(p.casefold() for p in relative[:2])==('skins','default'):result.append((root,relative[2:]))
   else:
    result.append((root,('ui',)+relative));result.append((root,relative))
  return result
 def resolve(self,path):
  key=clean_resource_path(path).replace('\\','/')
  cached=self.cache.get(key)
  try:
   if cached and cached.is_file():return cached
  except OSError:self.cache.pop(key,None)
  for root,parts in self.candidates(key):
   try:candidate=self.locate(root,parts)
   except OSError:continue
   if candidate:self.cache[key]=candidate;return candidate
  return None

class LayeredResources:
 """Resolve the original baseline, then overlay the active tab's mod files.

 Each layer keeps independent path/directory caches. No bitmap is decoded here.
 """
 def __init__(self,original_roots,mod_root=''):
  self.original=Resources(original_roots)
  self.mod=Resources([mod_root])
  # Image pickers use this order when converting absolute paths back to ui/ paths.
  self.roots=list(dict.fromkeys(self.mod.roots+self.original.roots))
 def resolve(self,path):
  original=self.original.resolve(path)
  replacement=self.mod.resolve(path)
  return replacement if replacement is not None else original
